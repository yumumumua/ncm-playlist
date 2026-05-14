"""网易云音乐 API 客户端 — 直接调用 music.163.com 接口"""

import json
import time
import urllib.request
import urllib.parse
import ssl


class NeteaseMusicAPI:
    """网易云音乐直接 API 客户端（基于网页端接口）。"""

    BASE_URL = "https://music.163.com"

    def __init__(self, cookie: str):
        self.cookie = cookie
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

    # ── 歌单接口 ──────────────────────────────────────────────

    def fetch_playlist_tracks(self, playlist_id: int) -> tuple[list, list]:
        """获取歌单全部歌曲，返回 (tracks, privileges)。

        使用分页，每页最多 500 首。
        """
        all_tracks = []
        all_privileges = []
        offset = 0
        page_size = 500

        while True:
            data = self.get("/api/v6/playlist/detail", {
                "id": playlist_id,
                "n": page_size,
                "offset": offset,
            })
            playlist = data.get("playlist", {})
            tracks = playlist.get("tracks", [])
            privileges = data.get("privileges", [])

            if not tracks:
                break

            all_tracks.extend(tracks)
            all_privileges.extend(privileges)

            if len(tracks) < page_size:
                break

            offset += len(tracks)
            time.sleep(0.3)

        return all_tracks, all_privileges

    def check_song_urls(self, song_ids: list[int]) -> dict[int, str | None]:
        """批量检查歌曲是否有可播放 URL。

        返回 {song_id: url_or_None}，每批 50 首。
        """
        result: dict[int, str | None] = {}
        batch_size = 50

        for i in range(0, len(song_ids), batch_size):
            batch = song_ids[i : i + batch_size]
            ids_str = ",".join(str(sid) for sid in batch)

            data = self.get("/api/song/enhance/player/url", {
                "id": ids_str,
                "ids": f"[{ids_str}]",
            })
            url_list = data.get("data", [])
            for item in url_list:
                result[item["id"]] = item.get("url")

            if i + batch_size < len(song_ids):
                time.sleep(0.3)

        return result

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
                    # 备用格式
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

            time.sleep(0.3)

        return ok, fail

    def add_tracks(self, playlist_id: int, track_ids: list[int]) -> tuple[int, int]:
        """向歌单添加歌曲。返回 (成功数, 失败数)。"""
        return self._manipulate_tracks("add", playlist_id, track_ids)

    def remove_tracks(self, playlist_id: int, track_ids: list[int]) -> tuple[int, int]:
        """从歌单移除歌曲。返回 (成功数, 失败数)。"""
        return self._manipulate_tracks("del", playlist_id, track_ids)
