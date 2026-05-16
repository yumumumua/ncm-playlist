---
name: ncm-playlist-classify
description: 网易云音乐歌单歌曲分类工具。根据用户定义的标准将歌曲分到不同歌单。
trigger:
  - 歌曲分类、歌单整理
  - 按类别分歌单、歌单歌曲归类
  - 歌单歌曲分类、批量归类歌曲
license: MIT
requires: Python 3.10+, ncm-playlist-tracks skill
---

# 网易云歌单歌曲分类 Skill

## 前置条件

- Python >= 3.10
- 有效的网易云音乐 Cookie（用户需从浏览器获取）
- 已安装 **ncm-playlist-tracks** skill（提供获取歌曲和添加歌曲的脚本）
- 用户已提前在网易云音乐中创建好目标歌单

## 依赖脚本

本 skill 不包含独立脚本，依赖 ncm-playlist-tracks 的脚本：

- **获取歌曲列表**: `skills/ncm-playlist-tracks/scripts/fetch_playlist.py`
- **添加歌曲到歌单**: `skills/ncm-playlist-tracks/scripts/manage_playlist.py`

## 工作流

### Step 1: 获取歌曲列表

使用 `fetch_playlist.py` 获取源歌单的所有歌曲：

```bash
cd <项目目录> && python3 skills/ncm-playlist-tracks/scripts/fetch_playlist.py \
  --cookie "COOKIE" \
  --playlist "<源歌单ID或链接>"
```

读取输出的 `output/songs.json`，每首歌包含 id、name、artists、album、privilege 等信息。

### Step 2: 确认分类标准

向用户询问分类维度和具体类别。示例分类方式：

| 维度 | 示例类别 |
|------|---------|
| 语言 | 华语、英语、日语、韩语、其他 |
| 风格 | 流行、摇滚、民谣、电子、古典、说唱 |
| 年代 | 80s、90s、00s、10s、20s |
| 自定义 | 用户自行定义的任意分类 |

确认最终的类别列表后进入下一步。

### Step 3: 收集目标歌单

要求用户为每个类别提供一个已存在的歌单 ID。以表格形式确认：

| 类别 | 目标歌单 ID |
|------|------------|
| 类别A | 用户提供的歌单ID |
| 类别B | 用户提供的歌单ID |

确保每个类别都有对应的歌单 ID。

### Step 4: 分类与分发

根据歌曲信息（name、artists、album）和用户定义的分类标准，判断每首歌的类别归属。

**分类策略：**
- 逐首读取 songs.json 中的歌曲
- 根据 name（歌名）、artists（歌手）、album（专辑）综合判断类别
- 将同一类别的歌曲 ID 收集到一起

**批量添加：**
每积累一批歌曲（最多 50 首），调用 `manage_playlist.py` 添加到对应歌单：

```bash
cd <项目目录> && python3 skills/ncm-playlist-tracks/scripts/manage_playlist.py \
  --cookie "COOKIE" \
  --playlist <目标歌单ID> \
  --add <id1,id2,...,id50>
```

**无法分类的歌曲：**
对于无法确定类别的歌曲，不执行添加操作，归入"未分类"列表在报告中提示用户。

### Step 5: 输出报告

分类完成后，向用户报告：

```
分类完成：
  华语: 35 首 → 歌单 12345678
  英语: 28 首 → 歌单 23456789
  日语: 12 首 → 歌单 34567890
  未分类: 3 首（请手动处理）

总计: 78 首已分类, 3 首未分类
```

## 注意事项

- 目标歌单必须由用户预先创建，本 skill 不负责创建歌单
- 分类判断基于歌曲的文本信息（歌名、歌手、专辑），由 AI 推理完成
- 批量添加复用 ncm-playlist-tracks 的分批逻辑（每批最多 50 首）
- 添加歌曲操作不可逆，分类前可先展示分类预览供用户确认
- Cookie 含敏感信息，通过命令行参数传入，不要硬编码
