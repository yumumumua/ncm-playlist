# 移除检查功能 + 添加进度显示 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 移除检查功能，为拉取和批量操作添加 .progress.json 进度文件机制，并用多线程加速歌单拉取。

**Architecture:** API 层新增可选的 progress_file 参数和线程安全的进度写入方法。fetch_playlist_tracks 使用 ThreadPoolExecutor 并行拉取分页。新建 fetch_playlist.py 替代 check_playlist.py。

**Tech Stack:** Python 3.10+，标准库（concurrent.futures, threading），零外部依赖。

---

## 依赖关系

```
Task 1 (删除检查功能)
  ↓
Task 2 (改造 api.py)
  ↓
Task 3 (新建 fetch_playlist.py)  ← 依赖 Task 2
Task 4 (改造 manage_playlist.py) ← 依赖 Task 2
  ↓
Task 5 (更新文档) ← 依赖 Task 3, 4
```

---

### Task 1: 删除检查功能

**Files:**
- Delete: `netease_music/checker.py`
- Delete: `check_playlist.py`
- Modify: `netease_music/__init__.py`

- [ ] **Step 1: 删除 checker.py**

```bash
rm netease_music/checker.py
```

- [ ] **Step 2: 删除 check_playlist.py**

```bash
rm check_playlist.py
```

- [ ] **Step 3: 更新 `__init__.py`，移除 checker 导出**

将 `netease_music/__init__.py` 内容改为：

```python
from .api import NeteaseMusicAPI
from .playlist import create_playlist, delete_playlist, add_tracks, remove_tracks
```

- [ ] **Step 4: 验证 import 无报错**

```bash
cd /Users/lin/project/ncm-playlist && python3 -c "from netease_music import NeteaseMusicAPI, create_playlist, delete_playlist, add_tracks, remove_tracks; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "refactor: remove checking functionality (checker.py, check_playlist.py)"
```

---

### Task 2: 改造 api.py

**Files:**
- Modify: `netease_music/api.py`

- [ ] **Step 1: 更新 api.py 完整内容**

将 `netease_music/api.py` 完整替换为以下内容：

```python
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
```

- [ ] **Step 2: 验证 import 无报错**

```bash
cd /Users/lin/project/ncm-playlist && python3 -c "from netease_music.api import NeteaseMusicAPI; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add netease_music/api.py && git commit -m "refactor: remove check_song_urls, add progress file and multithreading to api.py"
```

---

### Task 3: 新建 fetch_playlist.py

**Files:**
- Create: `fetch_playlist.py`

依赖：Task 2 完成

- [ ] **Step 1: 创建 `fetch_playlist.py`**

```python
#!/usr/bin/env python3
"""获取歌单歌曲列表。

用法：
  python fetch_playlist.py --cookie "COOKIE" --playlist "URL或ID"
  python fetch_playlist.py --cookie "COOKIE" --playlist "URL或ID" --output ./result
"""

import argparse
import json
import os
import sys
from urllib.parse import urlparse, parse_qs

from netease_music.api import NeteaseMusicAPI


def parse_playlist_id(raw: str) -> int:
    """从歌单链接或纯 ID 提取歌单 ID。"""
    raw = str(raw).strip()
    raw = raw.replace("\\?", "?").replace("\\=", "=").replace("\\&", "&")

    if "music.163.com" in raw or "://" in raw:
        parsed = urlparse(raw)
        params = parse_qs(parsed.query)
        ids = params.get("id", [])
        if ids:
            return int(ids[0])
        raise ValueError(f"无法从链接中提取歌单 ID: {raw}")

    if raw.isdigit():
        return int(raw)

    raise ValueError(f"无效的歌单输入: {raw}")


def format_songs(tracks: list, privileges: list) -> list[dict]:
    """格式化歌曲列表，附带 privilege 信息。"""
    priv_map = {p["id"]: p for p in privileges}
    songs = []
    for track in tracks:
        priv = priv_map.get(track["id"], {})
        songs.append({
            "id": track["id"],
            "name": track["name"],
            "artists": [ar["name"] for ar in track.get("ar", [])],
            "album": track.get("al", {}).get("name", ""),
            "duration_ms": track.get("dt", 0),
            "publish_time": track.get("publishTime", 0),
            "privilege": {
                "cp": priv.get("cp", 1),
                "pl": priv.get("pl", 0),
                "st": priv.get("st", 0),
            },
        })
    return songs


def main():
    parser = argparse.ArgumentParser(description="获取网易云音乐歌单歌曲列表")
    parser.add_argument("--cookie", required=True, help="网易云音乐 Cookie")
    parser.add_argument("--playlist", required=True, help="歌单链接或 ID")
    parser.add_argument("--output", default="output", help="输出目录 (默认: output)")
    args = parser.parse_args()

    try:
        playlist_id = parse_playlist_id(args.playlist)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    print(f"歌单 ID: {playlist_id}")

    os.makedirs(args.output, exist_ok=True)
    progress_file = os.path.join(args.output, ".progress.json")

    api = NeteaseMusicAPI(args.cookie, progress_file=progress_file)

    print("正在获取歌单歌曲...")
    tracks, privileges = api.fetch_playlist_tracks(playlist_id)
    print(f"共获取 {len(tracks)} 首歌曲")

    if not tracks:
        print("歌单为空或无法访问，请检查 Cookie 和歌单 ID")
        sys.exit(1)

    songs = format_songs(tracks, privileges)

    output_path = os.path.join(args.output, "songs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"\n结果已导出到 {output_path}")
    print(f"歌曲总数: {len(songs)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证语法正确**

```bash
cd /Users/lin/project/ncm-playlist && python3 -c "import py_compile; py_compile.compile('fetch_playlist.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add fetch_playlist.py && git commit -m "feat: add fetch_playlist.py entry script"
```

---

### Task 4: 改造 manage_playlist.py

**Files:**
- Modify: `manage_playlist.py`

依赖：Task 2 完成

- [ ] **Step 1: 更新 `manage_playlist.py` 完整内容**

将 `manage_playlist.py` 完整替换为以下内容：

```python
#!/usr/bin/env python3
"""歌单管理脚本 — 创建/删除歌单，添加/移除歌曲。

用法：
  # 创建歌单
  python manage_playlist.py --cookie "COOKIE" --create "歌单名称"

  # 删除歌单
  python manage_playlist.py --cookie "COOKIE" --delete 123456

  # 向歌单添加歌曲
  python manage_playlist.py --cookie "COOKIE" --playlist 123456 --add 111,222,333

  # 从歌单移除歌曲
  python manage_playlist.py --cookie "COOKIE" --playlist 123456 --remove-tracks 111,222,333

  # 设置歌单为公开
  python manage_playlist.py --cookie "COOKIE" --create "公开歌单" --public
"""

import argparse
import os
import sys

from netease_music.api import NeteaseMusicAPI


def main():
    parser = argparse.ArgumentParser(description="网易云音乐歌单管理工具")
    parser.add_argument("--cookie", required=True, help="网易云音乐 Cookie")
    parser.add_argument("--output", default="output", help="进度文件目录 (默认: output)")

    # 操作（互斥）
    ops = parser.add_mutually_exclusive_group(required=True)
    ops.add_argument("--create", metavar="NAME", help="创建歌单（指定名称）")
    ops.add_argument("--delete", type=int, metavar="ID", help="删除歌单（指定歌单 ID）")
    ops.add_argument("--add", metavar="ID1,ID2,...", help="向歌单添加歌曲（逗号分隔歌曲 ID）")
    ops.add_argument("--remove-tracks", metavar="ID1,ID2,...", help="从歌单移除歌曲（逗号分隔歌曲 ID）")

    # 附加参数
    parser.add_argument("--playlist", type=int, help="目标歌单 ID（添加/移除歌曲时必填）")
    parser.add_argument("--public", action="store_true", help="创建的歌单设为公开（默认隐私）")

    args = parser.parse_args()

    # 校验参数
    if args.add and not args.playlist:
        parser.error("添加歌曲需要 --playlist 参数")
    if args.remove_tracks and not args.playlist:
        parser.error("移除歌曲需要 --playlist 参数")

    os.makedirs(args.output, exist_ok=True)
    progress_file = os.path.join(args.output, ".progress.json")
    api = NeteaseMusicAPI(args.cookie, progress_file=progress_file)

    if args.create:
        privacy = 0 if args.public else 10
        pid = api.create_playlist(args.create, privacy)
        if pid:
            print(f"创建歌单「{args.create}」成功, id={pid}")
        else:
            print(f"创建歌单「{args.create}」失败")
            sys.exit(1)

    elif args.delete:
        ok = api.delete_playlist(args.delete)
        if ok:
            print(f"歌单 {args.delete} 删除成功")
        else:
            print(f"歌单 {args.delete} 删除失败")
            sys.exit(1)

    elif args.add:
        track_ids = [int(x.strip()) for x in args.add.split(",") if x.strip()]
        print(f"向歌单 {args.playlist} 添加 {len(track_ids)} 首歌曲...")
        ok, fail = api.add_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")

    elif args.remove_tracks:
        track_ids = [int(x.strip()) for x in args.remove_tracks.split(",") if x.strip()]
        print(f"从歌单 {args.playlist} 移除 {len(track_ids)} 首歌曲...")
        ok, fail = api.remove_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证语法正确**

```bash
cd /Users/lin/project/ncm-playlist && python3 -c "import py_compile; py_compile.compile('manage_playlist.py', doraise=True); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add manage_playlist.py && git commit -m "feat: add progress file support to manage_playlist.py"
```

---

### Task 5: 更新文档

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`

依赖：Task 3, Task 4 完成

- [ ] **Step 1: 更新 `SKILL.md` 完整内容**

将 `SKILL.md` 完整替换为以下内容：

```markdown
---
name: ncm-playlist
description: >
  网易云音乐歌单工具。获取歌单歌曲列表，管理歌单（创建/删除/添加/移除歌曲）。
  直接调用 music.163.com 网页端 API，零第三方依赖。
  触发场景：用户提到网易云音乐歌单整理、歌单管理、创建/删除歌单、
  往歌单添加或移除歌曲、歌单批量操作、获取歌单歌曲列表。
license: MIT
compatibility: Requires Python 3.10+
---

# 网易云音乐歌单工具

纯 Python 标准库实现，零第三方依赖，直连 music.163.com 网页端 API。

## 前置条件

- Python >= 3.10
- 有效的网易云音乐 Cookie（用户需从浏览器获取）

## 获取 Cookie

告知用户：
1. 浏览器打开 music.163.com 并登录
2. F12 → Network → 刷新 → 点击任意请求 → Request Headers → 复制完整 Cookie

## 脚本位置

入口脚本在项目根目录，核心模块在 `netease_music/` 包内。运行时先 cd 到项目目录：

```bash
cd <项目目录> && python3 fetch_playlist.py <参数>
cd <项目目录> && python3 manage_playlist.py <参数>
```

## 功能与用法

### 1. 获取歌单歌曲列表

```bash
python3 fetch_playlist.py \
  --cookie "COOKIE" \
  --playlist "歌单链接或ID"
```

输出到 `output/songs.json`，每首歌包含 id、name、artists、album、duration_ms、publish_time 和 privilege 字段（cp、pl、st）。

用户可根据 privilege 字段判断可播放性：`pl > 0` 可播放，`pl == 0` 不可播放。

可选参数：
- `--output DIR` — 指定输出目录（默认: output）

### 2. 歌单管理

```bash
# 创建歌单（默认隐私，加 --public 改为公开）
python3 manage_playlist.py --cookie "COOKIE" --create "歌单名"

# 删除歌单
python3 manage_playlist.py --cookie "COOKIE" --delete 歌单ID

# 添加歌曲
python3 manage_playlist.py --cookie "COOKIE" --playlist 歌单ID --add 111,222,333

# 移除歌曲
python3 manage_playlist.py --cookie "COOKIE" --playlist 歌单ID --remove-tracks 111,222,333
```

## Agent 进度追踪

拉取大歌单时，脚本会在输出目录写入 `.progress.json` 文件，格式：

```json
{"stage": "fetching", "current": 1500, "total": 5000}
```

大歌单建议用 Bash 工具的 `run_in_background: true` 运行脚本，然后轮询 `.progress.json` 查看进度。脚本正常完成后会删除此文件。

## privilege 字段说明

| 字段 | 含义 |
|------|------|
| `pl` | 播放等级，`> 0` 可播放，`== 0` 不可播放 |
| `cp` | 版权状态，`1` 有版权，`0` 无版权 |
| `st` | 状态，`0` 正常，负值异常（如 `-200` 有替代版本） |

## 文件结构

```
├── fetch_playlist.py         # 获取歌单歌曲列表
├── manage_playlist.py        # 歌单管理入口
└── netease_music/            # 核心模块包
    ├── __init__.py           # 包初始化
    ├── api.py                # API 客户端（直连 music.163.com）
    └── playlist.py           # 歌单操作封装
```

## 执行注意事项

- Cookie 含敏感信息，不要硬编码到脚本中，通过命令行参数传入
- 批量操作自动分批（每批 50 首），含频率限制等待
- 歌单操作（增删）不可逆，操作前确认用户意图
```

- [ ] **Step 2: 更新 `README.md`**

读取当前 README.md，将其内容替换为与 SKILL.md 一致的用户文档（去掉 frontmatter）。README.md 的内容应与 SKILL.md 的正文部分保持同步。

- [ ] **Step 3: 提交**

```bash
git add SKILL.md README.md && git commit -m "docs: update SKILL.md and README.md for new structure"
```

---

## Self-Review

**Spec coverage check:**
- 移除检查功能 → Task 1
- 新建 fetch_playlist.py → Task 3
- 多线程拉取 → Task 2 (api.py)
- .progress.json 进度文件 → Task 2 (api.py), Task 3, Task 4
- privilege 字段输出 → Task 3 (format_songs)
- 文档更新 → Task 5
- 所有 spec 要求已覆盖

**Placeholder scan:** 无 TBD/TODO，所有代码完整。

**Type consistency:** API 构造函数签名 `(cookie: str, progress_file: str | None = None)` 在所有任务中一致使用。
