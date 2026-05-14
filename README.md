# ncm-playlist

网易云音乐歌单管理 Agent Skill。纯 Python 标准库，零第三方依赖，直连 music.163.com 网页端 API。

## 功能

| 功能 | 说明 |
|------|------|
| 获取歌单歌曲列表 | 输入歌单 ID 或链接，获取完整歌曲列表（含 privilege 字段） |
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

- "帮我获取这个歌单的所有歌曲"
- "新建一个叫 XXX 的歌单"
- "往歌单里加这几首歌"

### 直接运行脚本

```bash
cd ncm-playlist
```

#### 1. 获取歌单歌曲列表

```bash
python3 fetch_playlist.py \
  --cookie "YOUR_COOKIE" \
  --playlist "歌单链接或ID"
```

输出到 `output/songs.json`，每首歌包含 id、name、artists、album、duration_ms、publish_time 和 privilege 字段。

可选参数：
- `--output DIR` — 指定输出目录

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

## privilege 字段说明

返回的歌曲列表中包含 privilege 字段，可用于判断歌曲是否可播放：

| 字段 | 含义 |
|------|------|
| `pl` | 播放等级，`> 0` 可播放，`== 0` 不可播放 |
| `cp` | 版权状态，`1` 有版权，`0` 无版权 |
| `st` | 状态，`0` 正常，负值异常（如 `-200` 有替代版本） |

## Agent 进度追踪

拉取大歌单时，脚本会在输出目录写入 `.progress.json` 文件：

```json
{"stage": "fetching", "current": 1500, "total": 5000}
```

建议用后台模式运行脚本，然后轮询 `.progress.json` 查看进度。脚本正常完成后会删除此文件。

## 文件结构

```
ncm-playlist/
├── SKILL.md                     # Agent Skill 元数据与指令
├── README.md                    # 本文件
├── fetch_playlist.py            # 获取歌单歌曲列表入口
├── manage_playlist.py           # 歌单管理入口（创建/删除/添加/移除）
└── netease_music/               # 核心模块包
    ├── __init__.py              # 包初始化
    ├── api.py                   # API 客户端（直连 music.163.com）
    └── playlist.py              # 歌单操作封装
```

## 注意事项

- Cookie 含敏感信息，通过命令行参数传入，不要硬编码
- 批量操作自动分批（每批 50 首），内置频率限制等待（0.3s/批）
- 歌单增删操作不可逆，操作前确认意图
- 网页端 API 非官方接口，网易云音乐可能随时变更

## License

MIT
