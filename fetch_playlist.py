#!/usr/bin/env python3
"""获取歌单歌曲列表。

用法：
  python fetch_playlist.py --cookie "COOKIE" --playlist "URL或ID"
  python fetch_playlist.py --cookie "COOKIE" --playlist "URL或ID" --output ./result
"""

import argparse
import json
import os
import sys
from urllib.parse import urlparse, parse_qs

from netease_music.api import NeteaseMusicAPI


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


def format_songs(tracks: list, privileges: list) -> list[dict]:
    """格式化歌曲列表，附带 privilege 信息。"""
    priv_map = {p["id"]: p for p in privileges}
    songs = []
    for track in tracks:
        priv = priv_map.get(track["id"], {})
        songs.append({
            "id": track["id"],
            "name": track["name"],
            "artists": [ar["name"] for ar in track.get("ar", [])],
            "album": track.get("al", {}).get("name", ""),
            "duration_ms": track.get("dt", 0),
            "publish_time": track.get("publishTime", 0),
            "privilege": {
                "cp": priv.get("cp", 1),
                "pl": priv.get("pl", 0),
                "st": priv.get("st", 0),
            },
        })
    return songs


def main():
    parser = argparse.ArgumentParser(description="获取网易云音乐歌单歌曲列表")
    parser.add_argument("--cookie", required=True, help="网易云音乐 Cookie")
    parser.add_argument("--playlist", required=True, help="歌单链接或 ID")
    parser.add_argument("--output", default="output", help="输出目录 (默认: output)")
    args = parser.parse_args()

    try:
        playlist_id = parse_playlist_id(args.playlist)
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    print(f"歌单 ID: {playlist_id}")

    os.makedirs(args.output, exist_ok=True)
    progress_file = os.path.join(args.output, ".progress.json")

    api = NeteaseMusicAPI(args.cookie, progress_file=progress_file)

    print("正在获取歌单歌曲...")
    tracks, privileges = api.fetch_playlist_tracks(playlist_id)
    print(f"共获取 {len(tracks)} 首歌曲")

    if not tracks:
        print("歌单为空或无法访问，请检查 Cookie 和歌单 ID")
        sys.exit(1)

    songs = format_songs(tracks, privileges)

    output_path = os.path.join(args.output, "songs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"\n结果已导出到 {output_path}")
    print(f"歌曲总数: {len(songs)}")


if __name__ == "__main__":
    main()
