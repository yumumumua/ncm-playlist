# ncm-playlist

网易云音乐歌单管理 Agent Skill。纯 Python 标准库，零第三方依赖，直连 music.163.com 网页端 API。

## 功能

| 功能 | 说明 |
|------|------|
| 获取歌单详情 | 输入歌单 ID 或链接，获取完整歌曲列表 |
| 不可播放检测 | 批量检测歌曲是否有可播放 URL（灰色歌曲） |
| 歌单清洗 | 一键过滤不可播放歌曲，交互确认后批量删除 |
| 新建歌单 | 创建公开或隐私歌单 |
| 删除歌单 | 删除指定歌单 |
| 添加歌曲 | 向歌单批量添加歌曲（自动分批，每批 50 首） |
| 移除歌曲 | 从歌单批量移除歌曲（自动分批，每批 50 首） |

## 前置条件

- Python >= 3.10
- 有效的网易云音乐 Cookie

## 获取 Cookie

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

## 使用方式

### 作为 Agent Skill 使用

安装后，当你在聊天中提到歌单管理相关需求时，agent 会自动激活此 skill。例如：

- "帮我整理一下这个歌单，把不能播放的歌删掉"
- "新建一个叫 XXX 的歌单"
- "往歌单里加这几首歌"

### 直接运行脚本

```bash
cd ncm-playlist
```

#### 1. 获取歌单并过滤不可播放歌曲

```bash
python3 check_playlist.py \
  --cookie "YOUR_COOKIE" \
  --playlist "歌单链接或ID"
```

输出到 `output/` 目录：
- `playable.json` — 可播放歌曲列表
- `unplayable.json` — 不可播放歌曲列表
- `summary.txt` — 摘要信息

可选参数：
- `--output DIR` — 指定输出目录
- `--remove` — 展示不可播放列表后交互确认是否从歌单删除

#### 2. 创建歌单

```bash
# 创建隐私歌单（默认）
python3 manage_playlist.py --cookie "YOUR_COOKIE" --create "我的歌单"

# 创建公开歌单
python3 manage_playlist.py --cookie "YOUR_COOKIE" --create "我的歌单" --public
```

#### 3. 删除歌单

```bash
python3 manage_playlist.py --cookie "YOUR_COOKIE" --delete 歌单ID
```

#### 4. 向歌单添加歌曲

```bash
python3 manage_playlist.py --cookie "YOUR_COOKIE" --playlist 歌单ID --add 111,222,333
```

#### 5. 从歌单移除歌曲

```bash
python3 manage_playlist.py --cookie "YOUR_COOKIE" --playlist 歌单ID --remove-tracks 111,222,333
```

## 不可播放的定义

歌单内原版本无法播放即属不可播放：
- 无版权
- 有替代版本（其他版本可播放但原版不行）
- 无法获取播放链接

## 文件结构

```
ncm-playlist/
├── SKILL.md                     # Agent Skill 元数据与指令
├── README.md                    # 本文件
├── check_playlist.py            # 歌单检查主脚本
├── manage_playlist.py           # 歌单管理入口（创建/删除/添加/移除）
└── netease_music/               # 核心模块包
    ├── __init__.py              # 包初始化
    ├── api.py                   # API 客户端（直连 music.163.com）
    ├── checker.py               # 可播放性判断逻辑
    └── playlist.py              # 歌单操作封装
```

## 注意事项

- Cookie 含敏感信息，通过命令行参数传入，不要硬编码
- 批量操作自动分批（每批 50 首），内置频率限制等待（0.3s/批）
- 歌单增删操作不可逆，操作前确认意图
- 网页端 API 非官方接口，网易云音乐可能随时变更

## License

MIT
