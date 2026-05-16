# Playlist Skill — 网易云歌单歌曲管理

本技能提供网易云音乐歌单歌曲管理能力，包括获取歌单歌曲、添加/移除歌曲等操作。

## 功能

| 功能 | 说明 |
|------|------|
| 获取歌单歌曲列表 | 输入歌单 ID 或链接，获取完整歌曲列表（含 privilege 字段） |
| 添加歌曲 | 向歌单批量添加歌曲（自动分批，每批 50 首） |
| 移除歌曲 | 从歌单批量移除歌曲（自动分批，每批 50 首） |

## 快速开始

```bash
# 获取歌单歌曲
python3 skills/playlist/scripts/fetch_playlist.py \
  --cookie "COOKIE" \
  --playlist "歌单ID或链接"

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
