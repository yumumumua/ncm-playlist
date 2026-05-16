---
name: ncm-playlist
description: 网易云音乐歌单管理工具。获取歌单歌曲列表，添加/移除歌单内歌曲。
trigger:
  - 网易云音乐歌单整理、歌单管理
  - 添加/移除歌单歌曲
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

### 2. 向歌单添加歌曲

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

### 3. 从歌单移除歌曲

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
- 歌单操作（增删歌曲）不可逆，操作前确认用户意图
