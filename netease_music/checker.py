"""可播放性检查 — 判断歌曲是否可播放，输出分类结果。"""

from __future__ import annotations


def _format_song(song: dict) -> dict:
    """提取歌曲关键信息。"""
    return {
        "id": song["id"],
        "name": song["name"],
        "artists": [ar["name"] for ar in song.get("ar", [])],
        "album": song.get("al", {}).get("name", ""),
        "duration_ms": song.get("dt", 0),
        "publish_time": song.get("publishTime", 0),
    }


def check_playability(
    tracks: list[dict],
    privileges: list[dict],
    url_map: dict[int, str | None] | None = None,
) -> dict:
    """根据 privileges 和 URL 检查每首歌的可播放状态。

    不可播放的定义：原版本无法播放（无 URL），包括：
    - 无版权 (noCopyrightRcmd / cp=0 & pl=0)
    - 有替代版本 (st=-200)
    - 其他原因无法播放

    返回:
        {
            "playable": [...],       # 可播放歌曲列表
            "unplayable": [...],     # 不可播放歌曲列表（含 reason 字段）
        }
    """
    priv_map = {p["id"]: p for p in privileges}
    playable = []
    unplayable = []

    for song in tracks:
        sid = song["id"]
        formatted = _format_song(song)
        priv = priv_map.get(sid, {})

        # 判断是否可播放：优先用 URL 检查，其次用 privileges 字段
        url_ok = url_map is not None and url_map.get(sid) is not None

        no_copy = song.get("noCopyrightRcmd")
        cp = priv.get("cp", 1)
        pl = priv.get("pl", 0)
        st = priv.get("st", 0)

        if url_ok:
            playable.append(formatted)
        elif no_copy:
            formatted["reason"] = f"无版权: {no_copy.get('typeDesc', '未知')}"
            unplayable.append(formatted)
        elif cp == 0 and pl == 0:
            formatted["reason"] = "无播放权限 (cp=0, pl=0)"
            unplayable.append(formatted)
        elif url_map is not None and not url_ok:
            # URL 检查明确返回 None
            if st == -200:
                formatted["reason"] = "有替代版本 (st=-200)"
            else:
                formatted["reason"] = "无法获取播放链接"
            unplayable.append(formatted)
        else:
            # 无 URL 信息时，仅凭 privileges 判断
            if st == -200:
                formatted["reason"] = "有替代版本 (st=-200)"
                unplayable.append(formatted)
            elif st < 0:
                formatted["reason"] = f"不可播放 (st={st})"
                unplayable.append(formatted)
            else:
                playable.append(formatted)

    return {"playable": playable, "unplayable": unplayable}
