# Refactor to Multi-Skill Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure ncm-playlist repository into a multi-skill architecture with skills/ directory, isolating the playlist skill into its own module for future extensibility.

**Architecture:**
- Create `skills/playlist/` as the isolated playlist skill module
- Move existing code into `skills/playlist/` with proper import path updates
- Rewrite SKILL.md to use "capability contract" format (input/output/call convention)
- Update root README.md to be a project overview

**Tech Stack:** Python 3.10+, Git, file system operations

---

## File Structure Map

**New files to create:**
- `skills/playlist/SKILL.md` — New skill contract format
- `skills/playlist/scripts/__init__.py` — Package marker (empty)

**Files to move:**
- `fetch_playlist.py` → `skills/playlist/scripts/fetch_playlist.py`
- `manage_playlist.py` → `skills/playlist/scripts/manage_playlist.py`
- `netease_music/__init__.py` → `skills/playlist/netease_music/__init__.py`
- `netease_music/api.py` → `skills/playlist/netease_music/api.py`

**Files to modify:**
- `skills/playlist/scripts/fetch_playlist.py` — Update import path
- `skills/playlist/scripts/manage_playlist.py` — Update import path
- `README.md` (root) — Rewrite as project overview
- `.gitignore` — Already updated (docs/specs/, CLAUDE.md)

**Files to delete:**
- `SKILL.md` (root) — Old format, replaced by skills/playlist/SKILL.md

---

## Task 1: Create Directory Structure

**Files:**
- Create: `skills/playlist/`
- Create: `skills/playlist/scripts/`
- Create: `skills/playlist/netease_music/`

- [ ] **Step 1: Create skills/playlist directory**

Run:
```bash
mkdir -p skills/playlist/scripts skills/playlist/netease_music
```

Expected: Directories created, no errors

- [ ] **Step 2: Verify directory creation**

Run:
```bash
ls -la skills/playlist/
```

Expected Output:
```
drwxr-xr-x  4 lin  staff  128 May 16 XX:XX .
drwxr-xr-x  3 lin  staff   96 May 16 XX:XX ..
drwxr-xr-x  2 lin  staff   64 May 16 XX:XX netease_music
drwxr-xr-x  2 lin  staff   64 May 16 XX:XX scripts
```

- [ ] **Step 3: Commit directory structure**

```bash
git add skills/
git commit -m "refactor: create skills/playlist directory structure"
```

---

## Task 2: Move and Update netease_music Module

**Files:**
- Move: `netease_music/__init__.py` → `skills/playlist/netease_music/__init__.py`
- Move: `netease_music/api.py` → `skills/playlist/netease_music/api.py`

- [ ] **Step 1: Move netease_music module files**

Run:
```bash
mv netease_music/__init__.py skills/playlist/netease_music/
mv netease_music/api.py skills/playlist/netease_music/
```

Expected: Files moved successfully

- [ ] **Step 2: Verify moved files**

Run:
```bash
ls -la skills/playlist/netease_music/
```

Expected Output:
```
drwxr-xr-x  4 lin  staff  128 May 16 XX:XX .
drwxr-xr-x  3 lin  staff   96 May 16 XX:XX ..
-rw-r--r--  1 lin  staff   XX May 16 XX:XX __init__.py
-rw-r--r--  1 lin  staff XXXX May 16 XX:XX api.py
```

- [ ] **Step 3: Verify old directory is empty or remove it**

Run:
```bash
rmdir netease_music 2>/dev/null || true
```

Expected: Old directory removed (if empty)

- [ ] **Step 4: Commit module move**

```bash
git add netease_music/ skills/playlist/netease_music/
git commit -m "refactor: move netease_music module to skills/playlist/"
```

---

## Task 3: Move and Update fetch_playlist.py

**Files:**
- Move: `fetch_playlist.py` → `skills/playlist/scripts/fetch_playlist.py`
- Modify: `skills/playlist/scripts/fetch_playlist.py:15` — Update import

- [ ] **Step 1: Move fetch_playlist.py**

Run:
```bash
mv fetch_playlist.py skills/playlist/scripts/
```

Expected: File moved successfully

- [ ] **Step 2: Create __init__.py for scripts package**

Run:
```bash
touch skills/playlist/scripts/__init__.py
```

Expected: Empty file created

- [ ] **Step 3: Update import path in fetch_playlist.py**

The file at line 15 has:
```python
from netease_music.api import NeteaseMusicAPI
```

Change to:
```python
import sys
from pathlib import Path

# Add parent directories to path for imports
script_dir = Path(__file__).parent
skill_root = script_dir.parent
sys.path.insert(0, str(skill_root))

from netease_music.api import NeteaseMusicAPI
```

Edit the file:
```bash
cat > skills/playlist/scripts/fetch_playlist.py << 'EOF'
#!/usr/bin/env python3
"""获取歌单歌曲列表。

用法：
  cd <项目根目录> && python3 skills/playlist/scripts/fetch_playlist.py --cookie "COOKIE" --playlist "URL或ID"
  cd <项目根目录> && python3 skills/playlist/scripts/fetch_playlist.py --cookie "COOKIE" --playlist "URL或ID" --output ./result
"""

import argparse
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Add parent directories to path for imports
script_dir = Path(__file__).parent
skill_root = script_dir.parent
sys.path.insert(0, str(skill_root))

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
EOF
```

Expected: File updated with new import logic

- [ ] **Step 4: Verify script syntax**

Run:
```bash
python3 -m py_compile skills/playlist/scripts/fetch_playlist.py
```

Expected: No syntax errors

- [ ] **Step 5: Commit fetch_playlist.py changes**

```bash
git add skills/playlist/scripts/fetch_playlist.py skills/playlist/scripts/__init__.py
git rm fetch_playlist.py
git commit -m "refactor: move and update fetch_playlist.py with new import paths"
```

---

## Task 4: Move and Update manage_playlist.py

**Files:**
- Move: `manage_playlist.py` → `skills/playlist/scripts/manage_playlist.py`
- Modify: `skills/playlist/scripts/manage_playlist.py:25` — Update import

- [ ] **Step 1: Move manage_playlist.py**

Run:
```bash
mv manage_playlist.py skills/playlist/scripts/
```

Expected: File moved successfully

- [ ] **Step 2: Update import path in manage_playlist.py**

The file at line 25 has:
```python
from netease_music.api import NeteaseMusicAPI
```

Change to include path setup (similar to fetch_playlist.py):

```bash
cat > skills/playlist/scripts/manage_playlist.py << 'EOF'
#!/usr/bin/env python3
"""歌单管理脚本 — 创建/删除歌单，添加/移除歌曲。

用法：
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --create "歌单名称"
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --delete 123456
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --playlist 123456 --add 111,222,333
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --playlist 123456 --remove-tracks 111,222,333
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directories to path for imports
script_dir = Path(__file__).parent
skill_root = script_dir.parent
sys.path.insert(0, str(skill_root))

from netease_music.api import NeteaseMusicAPI


def main():
    parser = argparse.ArgumentParser(description="网易云音乐歌单管理工具")
    parser.add_argument("--cookie", required=True, help="网易云音乐 Cookie")

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

    api = NeteaseMusicAPI(args.cookie)

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
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        progress_file = os.path.join(output_dir, ".progress.json")
        api.progress_file = progress_file
        print(f"向歌单 {args.playlist} 添加 {len(track_ids)} 首歌曲...")
        ok, fail = api.add_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")

    elif args.remove_tracks:
        track_ids = [int(x.strip()) for x in args.remove_tracks.split(",") if x.strip()]
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        progress_file = os.path.join(output_dir, ".progress.json")
        api.progress_file = progress_file
        print(f"从歌单 {args.playlist} 移除 {len(track_ids)} 首歌曲...")
        ok, fail = api.remove_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")


if __name__ == "__main__":
    main()
EOF
```

Expected: File updated with new import logic

- [ ] **Step 3: Verify script syntax**

Run:
```bash
python3 -m py_compile skills/playlist/scripts/manage_playlist.py
```

Expected: No syntax errors

- [ ] **Step 4: Commit manage_playlist.py changes**

```bash
git add skills/playlist/scripts/manage_playlist.py
git rm manage_playlist.py
git commit -m "refactor: move and update manage_playlist.py with new import paths"
```

---

## Task 5: Create New SKILL.md

**Files:**
- Create: `skills/playlist/SKILL.md`

- [ ] **Step 1: Create skills/playlist/SKILL.md with new contract format**

```bash
cat > skills/playlist/SKILL.md << 'EOF'
---
name: ncm-playlist
description: 网易云音乐歌单管理工具。获取歌单歌曲列表，管理歌单（创建/删除/添加/移除歌曲）。
trigger:
  - 网易云音乐歌单整理、歌单管理
  - 创建/删除歌单、添加/移除歌曲
  - 获取歌单歌曲列表、批量操作歌单
license: MIT
requires: Python 3.10+
---

# 网易云歌单管理 Skill

## 前置条件

- Python >= 3.10
- 有效的网易云音乐 Cookie（用户需从浏览器获取）

## 获取 Cookie

告知用户：
1. 浏览器打开 music.163.com 并登录
2. F12 → Network → 刷新 → 点击任意请求 → Request Headers → 复制完整 Cookie

## 脚本位置

入口脚本在 `skills/playlist/scripts/`，核心模块在 `skills/playlist/netease_music/` 包内。运行时先 cd 到项目根目录：

```bash
cd <项目目录> && python3 skills/playlist/scripts/fetch_playlist.py <参数>
cd <项目目录> && python3 skills/playlist/scripts/manage_playlist.py <参数>
```

## 能力列表

### 1. 获取歌单歌曲列表

**输入：**
- `playlist_id` (int) 或 `playlist_url` (str) — 歌单 ID 或完整链接

**输出：**
- JSON 文件 `output/songs.json`，每首歌包含：
  - `id`: 歌曲 ID
  - `name`: 歌曲名称
  - `artists`: 艺术家列表
  - `album`: 专辑名称
  - `duration_ms`: 时长（毫秒）
  - `publish_time`: 发布时间
  - `privilege`: 权限信息 {cp, pl, st}

**调用方式：**
```bash
cd <项目目录> && python3 skills/playlist/scripts/fetch_playlist.py \
  --cookie "COOKIE" \
  --playlist "<playlist_id_or_url>"
```

可选参数：
- `--output DIR` — 指定输出目录（默认: output）

### 2. 创建歌单

**输入：**
- `name` (str) — 歌单名称
- `public` (bool, 可选) — 是否公开，默认 false（隐私）

**输出：**
- 成功：打印 "创建歌单「名称」成功, id=<ID>"
- 失败：打印 "创建歌单「名称」失败"

**调用方式：**
```bash
cd <项目目录> && python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --create "<歌单名称>"

# 创建公开歌单
cd <项目目录> && python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --create "<歌单名称>" \
  --public
```

### 3. 删除歌单

**输入：**
- `playlist_id` (int) — 歌单 ID

**输出：**
- 成功：打印 "歌单 <ID> 删除成功"
- 失败：打印 "歌单 <ID> 删除失败"

**调用方式：**
```bash
cd <项目目录> && python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --delete <playlist_id>
```

### 4. 向歌单添加歌曲

**输入：**
- `playlist_id` (int) — 目标歌单 ID
- `track_ids` (list[int]) — 歌曲 ID 列表，逗号分隔

**输出：**
- 打印 "完成: 成功 <N>, 失败 <M>"

**调用方式：**
```bash
cd <项目目录> && python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --playlist <playlist_id> \
  --add <id1,id2,id3>
```

### 5. 从歌单移除歌曲

**输入：**
- `playlist_id` (int) — 目标歌单 ID
- `track_ids` (list[int]) — 歌曲 ID 列表，逗号分隔

**输出：**
- 打印 "完成: 成功 <N>, 失败 <M>"

**调用方式：**
```bash
cd <项目目录> && python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --playlist <playlist_id> \
  --remove-tracks <id1,id2,id3>
```

## 进度追踪

拉取大歌单时，脚本会在输出目录写入 `.progress.json` 文件：

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

## 注意事项

- Cookie 含敏感信息，不要硬编码到脚本中，通过命令行参数传入
- 批量操作自动分批（每批 50 首），含频率限制等待
- 歌单操作（增删）不可逆，操作前确认用户意图
EOF
```

Expected: File created with new skill contract format

- [ ] **Step 2: Verify SKILL.md exists**

Run:
```bash
ls -la skills/playlist/SKILL.md
```

Expected Output:
```
-rw-r--r--  1 lin  staff  XXXX May 16 XX:XX skills/playlist/SKILL.md
```

- [ ] **Step 3: Commit new SKILL.md**

```bash
git add skills/playlist/SKILL.md
git commit -m "refactor: create new SKILL.md with capability contract format"
```

---

## Task 6: Remove Old SKILL.md

**Files:**
- Delete: `SKILL.md` (root)

- [ ] **Step 1: Remove old SKILL.md from root**

```bash
git rm SKILL.md
```

Expected: File staged for removal

- [ ] **Step 2: Commit removal**

```bash
git commit -m "refactor: remove old SKILL.md from root directory"
```

---

## Task 7: Update Root README.md

**Files:**
- Modify: `README.md` (root)

- [ ] **Step 1: Rewrite README.md as project overview**

```bash
cat > README.md << 'EOF'
# ncm-playlist

网易云音乐管理 Agent Skill 集合。纯 Python 标准库，零第三方依赖，直连 music.163.com 网页端 API。

## 架构

本项目采用多技能架构，每个网易云音乐功能模块作为独立 skill 实现。

```
ncm-playlist/
├── skills/           # 技能目录
│   └── playlist/     # 歌单管理（当前）
│   ├── radio/        # 电台管理（规划中）
│   └── comment/      # 云村评论（规划中）
├── docs/             # 项目文档
└── README.md         # 本文件
```

## 当前技能

### playlist — 歌单管理

获取歌单歌曲列表、创建/删除歌单、添加/移除歌曲。

详见 [skills/playlist/SKILL.md](skills/playlist/SKILL.md) 或 [skills/playlist/README.md](skills/playlist/README.md)

## 前置条件

- Python >= 3.10
- 有效的网易云音乐 Cookie

### 获取 Cookie

1. 浏览器打开 [music.163.com](https://music.163.com) 并登录
2. F12 → Network → 刷新页面
3. 点击任意请求 → Request Headers → 复制完整 `Cookie` 值

## 安装

### 方式一：直接下载（通用）

适用于所有支持 AgentSkills 规范的 agent。

```bash
# 克隆到本地
git clone <repo-url> ncm-playlist

# 放到对应 agent 的 skills 目录
```

各平台的 skills 目录：

| Agent | 安装路径 |
|-------|---------|
| OpenClaw | `<workspace>/skills/ncm-playlist/` |
| Claude Code | `.agents/skills/ncm-playlist/` |
| OpenAI Codex | `.agents/skills/ncm-playlist/` |
| VS Code (Copilot) | `.agents/skills/ncm-playlist/` |
| Cursor | `.agents/skills/ncm-playlist/` |
| Gemini CLI | `.agents/skills/ncm-playlist/` |
| 其他 AgentSkills 兼容 agent | `.agents/skills/ncm-playlist/` |

示例：

```bash
# Claude Code
cp -r ncm-playlist/ .agents/skills/

# OpenClaw
cp -r ncm-playlist/ ~/.openclaw/workspace/skills/
```

### 方式二：OpenClaw ClawHub（仅 OpenClaw）

```bash
openclaw skills install ncm-playlist
```

## 快速开始

### 作为 Agent Skill 使用

安装后，当你在聊天中提到歌单管理相关需求时，agent 会自动激活此 skill。例如：

- "帮我获取这个歌单的所有歌曲"
- "新建一个叫 XXX 的歌单"
- "往歌单里加这几首歌"

### 直接运行脚本

```bash
cd ncm-playlist

# 获取歌单歌曲列表
python3 skills/playlist/scripts/fetch_playlist.py \
  --cookie "YOUR_COOKIE" \
  --playlist "歌单链接或ID"

# 创建歌单
python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "YOUR_COOKIE" \
  --create "我的歌单"

# 添加歌曲
python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "YOUR_COOKIE" \
  --playlist 歌单ID \
  --add 111,222,333
```

更多用法详见 [skills/playlist/SKILL.md](skills/playlist/SKILL.md)。

## License

MIT
EOF
```

Expected: README.md rewritten as project overview

- [ ] **Step 2: Commit README.md update**

```bash
git add README.md
git commit -m "refactor: update README.md as project overview"
```

---

## Task 8: Verify All Changes

**Files:**
- Verify: All moved files exist and work

- [ ] **Step 1: Verify complete directory structure**

Run:
```bash
find skills/playlist -type f -name "*.py" -o -name "*.md" | sort
```

Expected Output:
```
skills/playlist/SKILL.md
skills/playlist/netease_music/__init__.py
skills/playlist/netease_music/api.py
skills/playlist/scripts/__init__.py
skills/playlist/scripts/fetch_playlist.py
skills/playlist/scripts/manage_playlist.py
```

- [ ] **Step 2: Verify old files are removed**

Run:
```bash
ls -la | grep -E "fetch_playlist.py|manage_playlist.py|SKILL.md|netease_music"
```

Expected: No matches (old files removed)

- [ ] **Step 3: Test import path in fetch_playlist.py**

Run:
```bash
python3 -c "import sys; sys.path.insert(0, 'skills/playlist'); from netease_music.api import NeteaseMusicAPI; print('Import OK')"
```

Expected Output:
```
Import OK
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "refactor: complete skills structure refactor - all files moved and verified"
```

---

## Task 9: Create skills/playlist/README.md (Optional)

**Files:**
- Create: `skills/playlist/README.md`

- [ ] **Step 1: Create skill-specific README**

```bash
cat > skills/playlist/README.md << 'EOF'
# Playlist Skill — 网易云歌单管理

本技能提供网易云音乐歌单管理能力，包括获取歌单歌曲、创建/删除歌单、添加/移除歌曲等操作。

## 功能

| 功能 | 说明 |
|------|------|
| 获取歌单歌曲列表 | 输入歌单 ID 或链接，获取完整歌曲列表（含 privilege 字段） |
| 新建歌单 | 创建公开或隐私歌单 |
| 删除歌单 | 删除指定歌单 |
| 添加歌曲 | 向歌单批量添加歌曲（自动分批，每批 50 首） |
| 移除歌曲 | 从歌单批量移除歌曲（自动分批，每批 50 首） |

## 快速开始

```bash
# 获取歌单歌曲
python3 skills/playlist/scripts/fetch_playlist.py \
  --cookie "COOKIE" \
  --playlist "歌单ID或链接"

# 创建歌单
python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --create "我的歌单"

# 添加歌曲
python3 skills/playlist/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --playlist 歌单ID \
  --add 111,222,333
```

## 文件结构

```
skills/playlist/
├── SKILL.md              # Agent Skill 契约
├── README.md             # 本文件
├── scripts/              # 命令行脚本
│   ├── fetch_playlist.py
│   └── manage_playlist.py
└── netease_music/        # 核心模块
    ├── __init__.py
    └── api.py
```

## 更多信息

- 完整功能说明：见 [SKILL.md](SKILL.md)
- API 实现：见 [netease_music/api.py](netease_music/api.py)
EOF
```

Expected: File created

- [ ] **Step 2: Commit README**

```bash
git add skills/playlist/README.md
git commit -m "docs: add skill-specific README for playlist skill"
```

---

## Task 10: Final Verification and Cleanup

**Files:**
- Verify: Git status and working tree

- [ ] **Step 1: Check git status**

Run:
```bash
git status
```

Expected: Working tree clean (except for untracked docs/ and CLAUDE.md which are gitignored)

- [ ] **Step 2: Show commit history**

Run:
```bash
git log --oneline -10
```

Expected Output: Series of refactor commits showing the migration progress

- [ ] **Step 3: Show final tree structure**

Run:
```bash
tree -L 3 -I '__pycache__|*.pyc|.git' skills/
```

Expected Output:
```
skills/
└── playlist/
    ├── SKILL.md
    ├── README.md
    ├── netease_music/
    │   ├── __init__.py
    │   └── api.py
    └── scripts/
        ├── __init__.py
        ├── fetch_playlist.py
        └── manage_playlist.py
```

- [ ] **Step 4: Verify current branch**

Run:
```bash
git branch --show-current
```

Expected Output:
```
refactor/skills-structure
```

---

## Self-Review Results

**Spec coverage:** ✅ All requirements from design spec are implemented
- Directory structure: skills/playlist/ created ✅
- Files moved to new locations ✅
- Import paths updated ✅
- SKILL.md rewritten in contract format ✅
- Root README.md updated ✅
- .gitignore already updated ✅

**Placeholder scan:** ✅ No placeholders found
- All code blocks are complete
- All commands are exact
- All file paths are specified

**Type consistency:** ✅ Checked and consistent
- Import paths match across tasks
- File names are consistent
- Directory structure is consistent
