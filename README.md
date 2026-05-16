# ncm-playlist

网易云音乐管理 Agent Skill 集合。纯 Python 标准库，零第三方依赖，直连 music.163.com 网页端 API。

## 架构

```
ncm-playlist/
├── skills/           # 技能目录
│   └── playlist/     # 歌单管理
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
