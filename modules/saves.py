"""Manages world's save file. All actions are canceled if AVOID_SAVE setting is on."""

from modules import settings
from modules import position

import json
import os


SAVE_FILE = "./save.json"


def create_file():
    if settings.AVOID_SAVE:
        return
    if not os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "a+") as file:
            data = {"seed": settings.SEED, "chunks": {}}
            json.dump(data, file)


def remove_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)


def read_content() -> str | bool:
    with open(SAVE_FILE) as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return False


if not settings.AVOID_SAVE:
    create_file()
    content = read_content()
    if not content:
        remove_save()
        create_file()
        content = read_content()


def update(chunk, pos: position.Coordinate, voxel) -> None:
    """Updates saved world's state at provided chunk:pos"""
    if settings.AVOID_SAVE:
        return
    
    chunk_pos = f"{chunk.x}.{chunk.y}"
    if not chunk_pos in content.get("chunks"):
        content["chunks"][chunk_pos] = {}

    pos = f"{pos.x}.{pos.y}.{pos.z}"
    if voxel is not None:
        voxel = voxel.name
    content["chunks"][chunk_pos].update({pos: voxel})

    with open(SAVE_FILE, "w") as file:
        json.dump(content, file)


def get(chunk, pos) -> str | None | bool:
    """Returns voxel's name/None object if this position is saved or False if isn't."""
    if settings.AVOID_SAVE:
        return False
    
    chunk_pos = f"{chunk.x}.{chunk.y}"
    pos = f"{pos.x}.{pos.y}.{pos.z}"
    if chunk_pos not in content.get("chunks"):
        return False

    return content["chunks"][chunk_pos].get(pos, False)


def has_chunk(x: int, y: int) -> bool:
    """Check if save file has chunk data saved."""
    if settings.AVOID_SAVE:
        return False
    
    chunk_pos = f"{x}.{y}"
    return chunk_pos in content.get("chunks")


def get_chunk(x: int, y: int) -> dict:
    """Returns raw content of saved chunk's data."""
    if settings.AVOID_SAVE:
        return {}
    
    chunk_pos = f"{x}.{y}"
    if has_chunk(x, y):
        return content["chunks"][chunk_pos]
