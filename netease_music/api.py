"""网易云音乐 API 客户端 — 直接调用 music.163.com 接口"""

import json
import os
import time
import threading
import urllib.request
import urllib.parse
import ssl
from concurrent.futures import ThreadPoolExecutor


class NeteaseMusicAPI:
    """网易云音乐直接 API 客户端（基于网页端接口）。"""

    BASE_URL = "https://music.163.com"

    def __init__(self, cookie: str, progress_file: str | None = None):
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

    def get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def post(self, path: str, data: dict) -> dict:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            f"{self.BASE_URL}{path}", data=body, headers=self.headers
        )
        with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def post_json(self, path: str, data: dict) -> dict:
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

    def fetch_playlist_tracks(self, playlist_id: int) -> tuple[list, list]:
        """获取歌单全部歌曲，返回 (tracks, privileges)。

        第一页同步拉取获取总数，剩余页用 ThreadPoolExecutor(max_workers=3) 并行拉取。
        """
        page_size = 500

        # 第一页 — 同步，获取总数
        data = self.get("/api/v6/playlist/detail", {
            "id": playlist_id,
            "n": page_size,
            "offset": 0,
        })
        playlist_data = data.get("playlist", {})
        tracks = playlist_data.get("tracks", [])
        privileges = data.get("privileges", [])
        track_count = playlist_data.get("trackCount", len(tracks))

        if not tracks or len(tracks) >= track_count:
            return tracks, privileges

        # 多线程拉取剩余页
        offsets = list(range(page_size, track_count, page_size))
        total = track_count
        fetched = len(tracks)
        self._write_progress("fetching", fetched, total)

        remaining: dict[int, tuple[list, list]] = {}
        lock = threading.Lock()

        def fetch_page(offset: int):
            nonlocal fetched
            page_data = self.get("/api/v6/playlist/detail", {
                "id": playlist_id,
                "n": page_size,
                "offset": offset,
            })
            p = page_data.get("playlist", {})
            t = p.get("tracks", [])
            priv = page_data.get("privileges", [])
            with lock:
                remaining[offset] = (t, priv)
                fetched += len(t)
                self._write_progress("fetching", fetched, total)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch_page, off) for off in offsets]
            for future in futures:
                future.result()

        # 按 offset 排序合并
        all_tracks = list(tracks)
        all_privileges = list(privileges)
        for offset in sorted(remaining):
            t, p = remaining[offset]
            all_tracks.extend(t)
            all_privileges.extend(p)

        self._clear_progress()
        return all_tracks, all_privileges

    # ── 歌单操作 ──────────────────────────────────────────────

    def create_playlist(self, name: str, privacy: int = 10) -> int | None:
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

    def _manipulate_tracks(self, op: str, playlist_id: int, track_ids: list[int]) -> tuple[int, int]:
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

    def add_tracks(self, playlist_id: int, track_ids: list[int]) -> tuple[int, int]:
        """向歌单添加歌曲。返回 (成功数, 失败数)。"""
        return self._manipulate_tracks("add", playlist_id, track_ids)

    def remove_tracks(self, playlist_id: int, track_ids: list[int]) -> tuple[int, int]:
        """从歌单移除歌曲。返回 (成功数, 失败数)。"""
        return self._manipulate_tracks("del", playlist_id, track_ids)
