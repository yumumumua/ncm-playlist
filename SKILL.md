---
name: ncm-playlist
description: >
  网易云音乐歌单整理工具。获取歌单歌曲列表，检查并过滤不可播放歌曲，管理歌单（创建/删除/添加/移除歌曲）。
  直接调用 music.163.com 网页端 API，无需第三方依赖或代理服务。
  触发场景：用户提到网易云音乐歌单整理、歌单清洗、过滤不可播放歌曲、删除灰色歌曲、
  歌单管理、创建/删除歌单、往歌单添加或移除歌曲、歌单批量操作。
license: MIT
compatibility: Requires Python 3.10+
---

# 网易云音乐歌单整理

纯 Python 标准库实现，零第三方依赖，直连 music.163.com 网页端 API。

## 前置条件

- Python >= 3.10
- 有效的网易云音乐 Cookie（用户需从浏览器获取）

## 获取 Cookie

告知用户：
1. 浏览器打开 music.163.com 并登录
2. F12 → Network → 刷新 → 点击任意请求 → Request Headers → 复制完整 Cookie

## 脚本位置

所有脚本在 `scripts/` 目录下。运行时先 cd 到 skill 目录：

```bash
cd <skill目录> && python3 scripts/<脚本>.py <参数>
```

## 功能与用法

### 1. 获取歌单并过滤不可播放歌曲

```bash
python3 scripts/check_playlist.py \
  --cookie "COOKIE" \
  --playlist "歌单链接或ID"
```

输出到 `output/` 目录：`playable.json`、`unplayable.json`、`summary.txt`。

可选参数：
- `--output DIR` — 指定输出目录
- `--remove` — 展示不可播放列表后交互确认是否从歌单删除

### 2. 歌单管理

```bash
# 创建歌单（默认隐私，加 --public 改为公开）
python3 scripts/manage_playlist.py --cookie "COOKIE" --create "歌单名"

# 删除歌单
python3 scripts/manage_playlist.py --cookie "COOKIE" --delete 歌单ID

# 添加歌曲
python3 scripts/manage_playlist.py --cookie "COOKIE" --playlist 歌单ID --add 111,222,333

# 移除歌曲
python3 scripts/manage_playlist.py --cookie "COOKIE" --playlist 歌单ID --remove-tracks 111,222,333
```

## 不可播放的定义

歌单内原版本无法播放即属不可播放，包括：
- 无版权
- 有替代版本（其他版本可播放但原版不行）
- 无法获取播放链接

## 文件结构

```
scripts/
├── check_playlist.py   # 主脚本：获取歌单 + 过滤 + 可选删除
├── manage_playlist.py  # 歌单管理入口
├── api.py              # API 客户端（直连 music.163.com）
├── checker.py          # 可播放性判断逻辑
├── playlist.py         # 歌单操作封装
└── __init__.py
```

## 执行注意事项

- Cookie 含敏感信息，不要硬编码到脚本中，通过命令行参数传入
- 批量操作自动分批（每批 50 首），含频率限制等待
- 歌单操作（增删）不可逆，操作前确认用户意图
