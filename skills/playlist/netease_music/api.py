"""网易云音乐 API 客户端 — 直接调用 music.163.com 接口"""

import json
import os
import time
import threading
import urllib.request
import urllib.parse
import ssl
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Tuple, Dict


class NeteaseMusicAPI:
    """网易云音乐直接 API 客户端（基于网页端接口）。"""

    BASE_URL = "https://music.163.com"

    def __init__(self, cookie: str, progress_file: Optional[str] = None):
        self.cookie = cookie
        self.progress_file = progress_file
        self._progress_lock = threading.Lock()
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            "Cookie": cookie,
            "Referer": "https://music.163.com/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Origin": "https://music.163.com",
        }
        self._ssl_ctx = ssl.create_default_context()
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE

    # ── HTTP helpers ──────────────────────────────────────────

    def get(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{self.BASE_URL}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def post(self, path: str, data: Dict) -> Dict:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            f"{self.BASE_URL}{path}", data=body, headers=self.headers
        )
        with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def post_json(self, path: str, data: Dict) -> Dict:
        body = json.dumps(data).encode()
        hdrs = dict(self.headers)
        hdrs["Content-Type"] = "application/json"
        req = urllib.request.Request(
            f"{self.BASE_URL}{path}", data=body, headers=hdrs
        )
        with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())

    # ── 进度文件 ──────────────────────────────────────────────

    def _write_progress(self, stage: str, current: int, total: int):
        if not self.progress_file:
            return
        data = {"stage": stage, "current": current, "total": total}
        with self._progress_lock:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(data, f)

    def _clear_progress(self):
        if not self.progress_file:
            return
        with self._progress_lock:
            try:
                os.remove(self.progress_file)
            except FileNotFoundError:
                pass

    # ── 歌单接口 ──────────────────────────────────────────────

    def fetch_playlist_tracks(self, playlist_id: int) -> Tuple[List, List]:
        """获取歌单全部歌曲，返回 (tracks, privileges)。

        第一步：/api/v6/playlist/detail (n=0) 获取完整 trackIds 列表。
        第二步：分批调用 /api/v3/song/detail（每批 250 首）获取详情 + privilege。
        """
        detail_batch_size = 250

        # 获取完整 trackIds
        data = self.get("/api/v6/playlist/detail", {
            "id": playlist_id,
            "n": 0,
        })
        playlist_data = data.get("playlist", {})
        track_ids_obj = playlist_data.get("trackIds", [])
        track_count = len(track_ids_obj)

        if track_count == 0:
            # fallback: 尝试用 v6 自带的 tracks
            tracks = playlist_data.get("tracks", [])
            privileges = data.get("privileges", [])
            return tracks, privileges

        track_ids = [t["id"] for t in track_ids_obj]
        total = track_count
        fetched = 0
        self._write_progress("fetching", 0, total)

        # 分批获取歌曲详情
        remaining: Dict[int, Tuple[List, List]] = {}
        lock = threading.Lock()

        def fetch_detail_batch(batch_idx: int):
            nonlocal fetched
            start = batch_idx * detail_batch_size
            batch = track_ids[start:start + detail_batch_size]
            c_param = json.dumps([{"id": tid} for tid in batch])
            r = self.get("/api/v3/song/detail", {"c": c_param})
            t = r.get("songs", [])
            priv = r.get("privileges", [])
            with lock:
                remaining[batch_idx] = (t, priv)
                fetched += len(t)
                self._write_progress("fetching", fetched, total)

        num_batches = (track_count + detail_batch_size - 1) // detail_batch_size
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch_detail_batch, i) for i in range(num_batches)]
            for future in futures:
                future.result()

        # 按批次顺序合并
        all_tracks = []
        all_privileges = []
        for idx in range(num_batches):
            t, p = remaining.get(idx, ([], []))
            all_tracks.extend(t)
            all_privileges.extend(p)

        self._clear_progress()
        return all_tracks, all_privileges

    # ── 歌单操作 ──────────────────────────────────────────────

    def create_playlist(self, name: str, privacy: int = 10) -> Optional[int]:
        """创建歌单，返回歌单 ID 或 None。privacy: 10=隐私, 0=公开。"""
        result = self.post("/api/user/playlist/create", {
            "name": name,
            "privacy": str(privacy),
        })
        if result.get("code") == 200:
            return result.get("id") or result.get("playlist", {}).get("id")
        return None

    def delete_playlist(self, playlist_id: int) -> bool:
        """删除歌单。"""
        result = self.post("/api/user/playlist/delete", {
            "pid": str(playlist_id),
        })
        return result.get("code") == 200

    def _manipulate_tracks(self, op: str, playlist_id: int, track_ids: List[int]) -> Tuple[int, int]:
        """歌单歌曲增删通用方法。返回 (成功数, 失败数)。"""
        batch_size = 50
        ok = 0
        fail = 0
        total = len(track_ids)
        done = 0

        stage = "adding" if op == "add" else "removing"
        self._write_progress(stage, 0, total)

        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i : i + batch_size]
            tracks_str = "," + ",".join(str(tid) for tid in batch) + ","

            try:
                result = self.post("/api/playlist/manipulate/tracks", {
                    "op": op,
                    "pid": str(playlist_id),
                    "tracks": tracks_str,
                    "imme": "true",
                })
                if result.get("code") in (200, 512):
                    ok += len(batch)
                else:
                    result2 = self.post("/api/playlist/manipulate/tracks", {
                        "op": op,
                        "pid": str(playlist_id),
                        "trackIds": json.dumps(batch),
                        "imme": "true",
                    })
                    if result2.get("code") in (200, 512):
                        ok += len(batch)
                    else:
                        print(f"    批次 {i // batch_size + 1} 失败: "
                              f"code={result2.get('code')} msg={result2.get('message', '')}")
                        fail += len(batch)
            except Exception as e:
                print(f"    批次 {i // batch_size + 1} 异常: {e}")
                fail += len(batch)

            done += len(batch)
            self._write_progress(stage, done, total)
            time.sleep(0.3)

        self._clear_progress()
        return ok, fail

    def add_tracks(self, playlist_id: int, track_ids: List[int]) -> Tuple[int, int]:
        """向歌单添加歌曲。返回 (成功数, 失败数)。"""
        return self._manipulate_tracks("add", playlist_id, track_ids)

    def remove_tracks(self, playlist_id: int, track_ids: List[int]) -> Tuple[int, int]:
        """从歌单移除歌曲。返回 (成功数, 失败数)。"""
        return self._manipulate_tracks("del", playlist_id, track_ids)
