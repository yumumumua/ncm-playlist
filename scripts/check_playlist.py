#!/usr/bin/env python3
"""获取歌单歌曲列表，过滤不可播放歌曲。

功能：
  1. 获取歌单全部歌曲
  2. 检查每首歌的可播放状态
  3. 输出可播放 / 不可播放列表
  4. 可选：从歌单中删除不可播放歌曲（需 --remove）

用法：
  python check_playlist.py --cookie "COOKIE" --playlist "URL或ID"
  python check_playlist.py --cookie "COOKIE" --playlist "URL或ID" --remove
  python check_playlist.py --cookie "COOKIE" --playlist "URL或ID" --output ./result
"""

import argparse
import json
import os
import sys
from urllib.parse import urlparse, parse_qs

from netease_music.api import NeteaseMusicAPI
from netease_music.checker import check_playability


def parse_playlist_id(raw: str) -> int:
    """从歌单链接或纯 ID 提取歌单 ID。"""
    raw = str(raw).strip()
    raw = raw.replace("\\?", "?").replace("\\=", "=").replace("\\&", "&")

    if "music.163.com" in raw or "://" in raw:
        parsed = urlparse(raw)
        params = parse_qs(parsed.query)
        ids = params.get("id", [])
        if ids:
            return int(ids[0])
        raise ValueError(f"无法从链接中提取歌单 ID: {raw}")

    if raw.isdigit():
        return int(raw)

    raise ValueError(f"无效的歌单输入: {raw}")


def export_results(classified: dict, output_dir: str):
    """导出结果到 JSON 文件。"""
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "playable.json"), "w", encoding="utf-8") as f:
        json.dump(classified["playable"], f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "unplayable.json"), "w", encoding="utf-8") as f:
        json.dump(classified["unplayable"], f, ensure_ascii=False, indent=2)

    # 可读摘要
    playable = classified["playable"]
    unplayable = classified["unplayable"]
    lines = [
        "歌单过滤结果",
        "=" * 50,
        f"总歌曲数: {len(playable) + len(unplayable)}",
        f"可播放: {len(playable)}",
        f"不可播放: {len(unplayable)}",
        "",
    ]
    if unplayable:
        lines.append("─" * 50)
        lines.append("不可播放歌曲:")
        for s in unplayable:
            artists = ", ".join(s["artists"])
            lines.append(f"  [{s['id']}] {s['name']} - {artists}  ({s.get('reason', '')})")
    if playable:
        lines.append("─" * 50)
        lines.append("可播放歌曲:")
        for s in playable:
            artists = ", ".join(s["artists"])
            lines.append(f"  [{s['id']}] {s['name']} - {artists}")

    with open(os.path.join(output_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def print_summary(classified: dict):
    """控制台打印摘要。"""
    playable = classified["playable"]
    unplayable = classified["unplayable"]
    total = len(playable) + len(unplayable)

    print(f"\n{'=' * 50}")
    print(f"总歌曲数: {total}")
    print(f"可播放: {len(playable)}")
    print(f"不可播放: {len(unplayable)}")

    if unplayable:
        print(f"\n{'─' * 50}")
        print("不可播放歌曲:")
        for s in unplayable:
            artists = ", ".join(s["artists"])
            print(f"  [{s['id']}] {s['name']} - {artists}  ({s.get('reason', '')})")


def main():
    parser = argparse.ArgumentParser(
        description="网易云音乐歌单过滤工具 — 获取并过滤不可播放歌曲"
    )
    parser.add_argument("--cookie", required=True, help="网易云音乐 Cookie")
    parser.add_argument("--playlist", required=True, help="歌单链接或 ID")
    parser.add_argument("--output", default="output", help="输出目录 (默认: output)")
    parser.add_argument(
        "--remove",
        action="store_true",
        help="交互确认后从歌单中删除不可播放歌曲",
    )
    args = parser.parse_args()

    # 1. 解析歌单 ID
    try:
        playlist_id = parse_playlist_id(args.playlist)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    print(f"歌单 ID: {playlist_id}")

    # 2. 初始化 API
    api = NeteaseMusicAPI(args.cookie)

    # 3. 获取歌单歌曲
    print("正在获取歌单歌曲...")
    tracks, privileges = api.fetch_playlist_tracks(playlist_id)
    print(f"共获取 {len(tracks)} 首歌曲")

    if not tracks:
        print("歌单为空或无法访问，请检查 Cookie 和歌单 ID")
        sys.exit(1)

    # 4. 检查播放链接（可选，更准确）
    print("正在检查播放链接...")
    song_ids = [t["id"] for t in tracks]
    url_map = api.check_song_urls(song_ids)

    # 5. 分类
    classified = check_playability(tracks, privileges, url_map)
    print_summary(classified)

    # 6. 导出
    export_results(classified, args.output)
    print(f"\n结果已导出到 {args.output}/ 目录")

    # 7. 可选：删除不可播放歌曲
    if args.remove and classified["unplayable"]:
        print(f"\n{'=' * 50}")
        print(f"发现 {len(classified['unplayable'])} 首不可播放歌曲")
        confirm = input("是否从歌单中删除这些歌曲？(y/N): ").strip().lower()
        if confirm == "y":
            unplayable_ids = [s["id"] for s in classified["unplayable"]]
            print(f"正在从歌单中移除 {len(unplayable_ids)} 首歌曲...")
            ok, fail = api.remove_tracks(playlist_id, unplayable_ids)
            print(f"移除完成: 成功 {ok}, 失败 {fail}")
        else:
            print("已取消删除操作")
    elif args.remove and not classified["unplayable"]:
        print("\n没有不可播放的歌曲，无需删除")


if __name__ == "__main__":
    main()
