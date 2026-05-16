#!/usr/bin/env python3
"""歌单管理脚本 — 创建/删除歌单，添加/移除歌曲。

用法：
  # 创建歌单
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --create "歌单名称"

  # 删除歌单
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --delete 123456

  # 向歌单添加歌曲
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --playlist 123456 --add 111,222,333

  # 从歌单移除歌曲
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --playlist 123456 --remove-tracks 111,222,333

  # 设置歌单为公开
  cd <项目根目录> && python3 skills/playlist/scripts/manage_playlist.py --cookie "COOKIE" --create "公开歌单" --public
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
    parser = argparse.ArgumentParser(description="网易云音乐歌单管理工具")
    parser.add_argument("--cookie", required=True, help="网易云音乐 Cookie")

    # 操作（互斥）
    ops = parser.add_mutually_exclusive_group(required=True)
    ops.add_argument("--create", metavar="NAME", help="创建歌单（指定名称）")
    ops.add_argument("--delete", type=int, metavar="ID", help="删除歌单（指定歌单 ID）")
    ops.add_argument("--add", metavar="ID1,ID2,...", help="向歌单添加歌曲（逗号分隔歌曲 ID）")
    ops.add_argument("--remove-tracks", metavar="ID1,ID2,...", help="从歌单移除歌曲（逗号分隔歌曲 ID）")

    # 附加参数
    parser.add_argument("--playlist", type=int, help="目标歌单 ID（添加/移除歌曲时必填）")
    parser.add_argument("--public", action="store_true", help="创建的歌单设为公开（默认隐私）")

    args = parser.parse_args()

    # 校验参数
    if args.add and not args.playlist:
        parser.error("添加歌曲需要 --playlist 参数")
    if args.remove_tracks and not args.playlist:
        parser.error("移除歌曲需要 --playlist 参数")

    api = NeteaseMusicAPI(args.cookie)

    if args.create:
        privacy = 0 if args.public else 10
        pid = api.create_playlist(args.create, privacy)
        if pid:
            print(f"创建歌单「{args.create}」成功, id={pid}")
        else:
            print(f"创建歌单「{args.create}」失败")
            sys.exit(1)

    elif args.delete:
        ok = api.delete_playlist(args.delete)
        if ok:
            print(f"歌单 {args.delete} 删除成功")
        else:
            print(f"歌单 {args.delete} 删除失败")
            sys.exit(1)

    elif args.add:
        track_ids = [int(x.strip()) for x in args.add.split(",") if x.strip()]
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        progress_file = os.path.join(output_dir, ".progress.json")
        api.progress_file = progress_file
        print(f"向歌单 {args.playlist} 添加 {len(track_ids)} 首歌曲...")
        ok, fail = api.add_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")

    elif args.remove_tracks:
        track_ids = [int(x.strip()) for x in args.remove_tracks.split(",") if x.strip()]
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        progress_file = os.path.join(output_dir, ".progress.json")
        api.progress_file = progress_file
        print(f"从歌单 {args.playlist} 移除 {len(track_ids)} 首歌曲...")
        ok, fail = api.remove_tracks(args.playlist, track_ids)
        print(f"完成: 成功 {ok}, 失败 {fail}")


if __name__ == "__main__":
    main()
