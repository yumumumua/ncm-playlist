#!/usr/bin/env python3
"""歌单歌曲管理脚本 — 向歌单添加/移除歌曲。

用法：
  # 向歌单添加歌曲
  cd <项目根目录> && python3 skills/ncm-playlist-tracks/scripts/manage_playlist.py --cookie "COOKIE" --playlist 123456 --add 111,222,333

  # 从歌单移除歌曲
  cd <项目根目录> && python3 skills/ncm-playlist-tracks/scripts/manage_playlist.py --cookie "COOKIE" --playlist 123456 --remove-tracks 111,222,333
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
    parser = argparse.ArgumentParser(description="网易云音乐歌单歌曲管理工具")
    parser.add_argument("--cookie", required=True, help="网易云音乐 Cookie")
    parser.add_argument("--playlist", type=int, required=True, help="目标歌单 ID")

    # 操作（互斥）
    ops = parser.add_mutually_exclusive_group(required=True)
    ops.add_argument("--add", metavar="ID1,ID2,...", help="向歌单添加歌曲（逗号分隔歌曲 ID）")
    ops.add_argument("--remove-tracks", metavar="ID1,ID2,...", help="从歌单移除歌曲（逗号分隔歌曲 ID）")

    args = parser.parse_args()

    api = NeteaseMusicAPI(args.cookie)
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    progress_file = os.path.join(output_dir, ".progress.json")
    api.progress_file = progress_file

    if args.add:
        track_ids = [int(x.strip()) for x in args.add.split(",") if x.strip()]
        print(f"向歌单 {args.playlist} 添加 {len(track_ids)} 首歌曲...")
        ok, fail = api.add_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")

    elif args.remove_tracks:
        track_ids = [int(x.strip()) for x in args.remove_tracks.split(",") if x.strip()]
        print(f"从歌单 {args.playlist} 移除 {len(track_ids)} 首歌曲...")
        ok, fail = api.remove_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")


if __name__ == "__main__":
    main()
