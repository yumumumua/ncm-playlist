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
