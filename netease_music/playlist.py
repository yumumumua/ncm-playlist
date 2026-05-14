"""歌单 CRUD 封装 — 对外提供简洁函数。"""

from .api import NeteaseMusicAPI


def create_playlist(api: NeteaseMusicAPI, name: str, privacy: int = 10) -> int | None:
    """创建歌单，返回歌单 ID 或 None。"""
    pid = api.create_playlist(name, privacy)
    if pid:
        print(f"  创建歌单「{name}」成功, id={pid}")
    else:
        print(f"  创建歌单「{name}」失败")
    return pid


def delete_playlist(api: NeteaseMusicAPI, playlist_id: int) -> bool:
    """删除歌单。"""
    ok = api.delete_playlist(playlist_id)
    if ok:
        print(f"  歌单 {playlist_id} 删除成功")
    else:
        print(f"  歌单 {playlist_id} 删除失败")
    return ok


def add_tracks(api: NeteaseMusicAPI, playlist_id: int, track_ids: list[int]) -> tuple[int, int]:
    """向歌单添加歌曲。返回 (成功数, 失败数)。"""
    ok, fail = api.add_tracks(playlist_id, track_ids)
    print(f"  歌单 {playlist_id}: 添加 {ok} 首, 失败 {fail} 首")
    return ok, fail


def remove_tracks(api: NeteaseMusicAPI, playlist_id: int, track_ids: list[int]) -> tuple[int, int]:
    """从歌单移除歌曲。返回 (成功数, 失败数)。"""
    ok, fail = api.remove_tracks(playlist_id, track_ids)
    print(f"  歌单 {playlist_id}: 移除 {ok} 首, 失败 {fail} 首")
    return ok, fail
