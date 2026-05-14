# 移除检查功能 + 添加进度显示设计

## 背景

当前 ncm-playlist 做了两件事：获取歌单歌曲 + 检查歌曲可播放性。检查功能不属于此工具的职责，用户拿到歌曲列表后可根据 privilege 字段自行判断。同时，拉取大歌单时耗时长且无进度反馈，Agent 无法区分"正在处理"和"脚本卡死"。

## 变更概览

1. 移除检查相关功能（checker.py、check_playlist.py、check_song_urls）
2. 新建 fetch_playlist.py 作为拉取歌单歌曲的入口
3. fetch_playlist_tracks 改为多线程拉取，提升速度
4. 拉取和批量操作过程中写 .progress.json 文件供 Agent 轮询
5. 歌曲输出中包含 privilege 字段（cp, pl, st），用户可据此判断可播放性

## 详细设计

### 1. 移除检查功能

**删除文件**：
- `netease_music/checker.py`
- `check_playlist.py`

**修改 `api.py`**：
- 移除 `check_song_urls` 方法

**修改 `__init__.py`**：
- 移除 `from .checker import check_playability`

### 2. 新建 fetch_playlist.py

CLI 入口脚本，负责拉取歌单全部歌曲并输出 JSON。

**参数**：
- `--cookie`（必填）：网易云音乐 Cookie
- `--playlist`（必填）：歌单链接或 ID
- `--output`（可选）：输出目录，默认 `output`

**输出**：
- `output/songs.json`：歌曲列表，每首歌包含以下字段：
  ```json
  {
    "id": 123,
    "name": "歌曲名",
    "artists": ["歌手1", "歌手2"],
    "album": "专辑名",
    "duration_ms": 240000,
    "publish_time": 1234567890000,
    "privilege": {
      "cp": 1,
      "pl": 320000,
      "st": 0
    }
  }
  ```
- `output/.progress.json`：处理过程中的进度文件，完成后删除

**执行流程**：
1. 解析歌单 ID（复用现有的 parse_playlist_id 逻辑）
2. 初始化 API，创建输出目录
3. 写 `.progress.json`：`{"stage": "fetching", "current": 0, "total": 0}`
4. 调用 `fetch_playlist_tracks`（已含进度更新）
5. 格式化输出歌曲列表（含 privilege 字段）
6. 写入 `songs.json`
7. 删除 `.progress.json`
8. 打印摘要：歌单 ID、歌曲总数、输出路径

### 3. 多线程拉取（api.py 改造）

**fetch_playlist_tracks 改造**：

```
原流程：同步逐页拉取，每页 300ms 延迟
新流程：
  1. 同步拉取第一页，获取 playlist.trackCount（总曲目数）
  2. 若总曲目 <= 500，直接返回
  3. 计算剩余页 offset 列表
  4. 使用 concurrent.futures.ThreadPoolExecutor(max_workers=3) 并行拉取
  5. 每页完成后更新 .progress.json
  6. 所有页完成后按 offset 排序合并结果
```

**并发控制**：
- max_workers=3（避免触发 API 限频）
- 每个线程内的请求保持原有超时设置（30s）
- 无需额外的 sleep 延迟（并发数已足够保守）

**进度更新**：
- 使用 threading.Lock 保护 .progress.json 的写入
- 每完成一页更新 current 计数

### 4. 进度文件机制

**.progress.json 格式**：

拉取阶段：
```json
{"stage": "fetching", "current": 1500, "total": 5000}
```

批量操作阶段（添加/移除歌曲）：
```json
{"stage": "adding", "current": 100, "total": 500}
```

```json
{"stage": "removing", "current": 100, "total": 500}
```

**生命周期**：
- 开始处理时创建
- 每完成一个批次/页时更新
- 正常完成后删除
- 异常退出时残留（Agent 可据此判断脚本中断）

**写入方式**：
- 使用 threading.Lock（多线程场景下保护文件写入）
- 每次覆盖写入（非追加）

**Agent 使用方式**（SKILL.md 中说明）：
1. 使用 Bash 工具的 `run_in_background: true` 运行脚本
2. 通过 Read 工具轮询 `output/.progress.json` 查看进度
3. 脚本完成后收到通知，读取 `output/songs.json` 获取结果

### 5. _manipulate_tracks 进度更新

在 `_manipulate_tracks` 方法中：
- 开始时写 `.progress.json`：`{"stage": "adding/removing", "current": 0, "total": N}`
- 每完成一批（50 首）更新 current
- 全部完成后删除 `.progress.json`

### 6. 文件结构（变更后）

```
├── fetch_playlist.py         # 拉取歌单歌曲入口（新建）
├── manage_playlist.py        # 歌单管理入口（不变）
├── netease_music/
│   ├── __init__.py           # 移除 checker 导出
│   ├── api.py                # 移除 check_song_urls，加多线程+进度
│   └── playlist.py           # 不变
├── SKILL.md                  # 更新文档
└── README.md                 # 更新文档
```

### 7. 歌曲输出中的 privilege 字段

每首歌附带 privilege 信息，用户/Agent 可据此判断可播放性：
- `pl > 0`：可播放（值代表音质等级）
- `pl == 0`：不可播放
- `cp == 0`：无版权
- `st < 0`：状态异常（如 st=-200 表示有替代版本）

## 不做的事

- 不引入 tqdm 或其他外部依赖（保持零依赖）
- 不做可播放性判断逻辑（由用户/Agent 根据 privilege 字段自行处理）
- 不做 ETA 预估（进度文件只报已完成量）
