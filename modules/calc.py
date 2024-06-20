"""Module contains multiple helper functions."""

from modules import position
from modules import settings

from functools import lru_cache
from typing import Any
import pygame
import time


FACE_MAP = open("./res/face_map.txt").read().split("\n")


class CombinedRange:
    """Object contains multiple range() instances.
    Checks for value's containment in every range."""

    def __init__(self, *ranges) -> None:
        self.ranges = ranges

    def __contains__(self, value: int) -> bool:
        for r in self.ranges:
            if value in r:
                return True
        return False


def interpolation(set1: list, set2: list, x):
    return set1[1] + (x - set1[0]) * ((set2[1] - set1[1]) / (set2[0] - set1[0]))
    
    
@lru_cache
def calc_tile_pos(x: int, y: int, z: int) -> tuple[int, int]:
    new_x = (x * 32 + y * -32) - 32 + settings.SCREEN_WIDTH // 2
    new_y = (x * 16 + y * 16) - (16 * z) + settings.SCREEN_HEIGHT // 3
    return new_x, new_y


def rect_ranges(rect: pygame.Rect) -> tuple[range, range]:
    """Returns X and Y values as ranges."""
    return (
        range(rect.x, rect.x + rect.width + 1),
        range(rect.y, rect.y + rect.height + 1),
    )


def rects_intersection(r1: pygame.Rect, r2: pygame.Rect) -> pygame.Rect:
    """Create new rect being result of the intersection of two rects."""
    left = max(r1.left, r2.left)
    right = min(r1.right, r2.right)
    top = max(r1.top, r2.top)
    bottom = min(r1.bottom, r2.bottom)
    return pygame.Rect(left, top, (right - left), (bottom - top))


def is_in_real_rect(x: int, y: int, r: pygame.Rect) -> bool:
    """Checks if mouse cursor is in block's real rect (avoiding transparent)."""
    mx = x - r.x
    my = y - r.y

    if mx not in range(0, 64) or my not in range(0, 64):
        return False

    face = FACE_MAP[my][mx]
    return face != "0"


def calc_block_face(x: int, y: int, r: pygame.Rect) -> position.BlockFace | None:
    """Check on wich block's face cursor is poiting."""
    mx = x - r.x
    my = y - r.y

    face_name = FACE_MAP[my][mx]

    return {
        "0": position.BlockFace.NONE,
        "T": position.BlockFace.TOP,
        "L": position.BlockFace.LEFT,
        "R": position.BlockFace.RIGHT,
    }.get(face_name)


def flatten2d(list2d: list[list[Any]]) -> list:
    """Flattens 2-dimensional array."""
    return [x for xs in list2d for x in xs]


def is_all_none(arr: list[Any] | list[list[Any]]) -> bool:
    """Determines if all items in array are NoneType. Accepts 1d and 2d lists."""
    if isinstance(arr[0], list):
        arr = flatten2d(arr)
    return arr.count(None) == len(arr)


def get_bounding_chunks_pos(x: int, y: int) -> list[tuple[int, int]]:
    """Returns locations of chunks surrounding chunk at (x, y)."""
    n = (x, y + 1)
    ne = (x + 1, y + 1)
    e = (x + 1, y)
    se = (x + 1, y - 1)
    s = (x, y - 1)
    sw = (x - 1, y - 1)
    w = (x - 1, y)
    nw = (x - 1, y + 1)

    bounding = [n, ne, e, se, s, sw, w, nw]
    return bounding


def get_cross_bounding_pos(
    pos: position.Coordinate,
) -> dict[position.AngleDirection, position.Coordinate]:
    """Returns all voxels positions on the N,S,W,E positions from pos."""
    bounding = {}
    for angle, p in {
        position.AngleDirection.N: pos.add_y(-1),
        position.AngleDirection.E: pos.add_x(1),
        position.AngleDirection.S: pos.add_y(1),
        position.AngleDirection.W: pos.add_x(-1),
    }.items():
        if (
            pos.x >= 0
            and pos.y >= 0
            and pos.x < settings.CHUNK_SIZE
            and pos.y < settings.CHUNK_SIZE
        ):
            bounding.update({angle: p})
    return bounding


def calc_time_bg_index() -> int:
    """Used for setting background image based on time."""
    hour = time.localtime().tm_hour

    if hour in CombinedRange(range(23, 24), range(0, 6)):
        return 2

    if hour in CombinedRange(range(6, 9), range(19, 23)):
        return 1

    return 0


def get_outline(image: pygame.Surface, color=(239, 149, 37)) -> pygame.Surface:
    """Creates outline of any pygame's Surface object."""
    rect = image.get_rect()
    mask = pygame.mask.from_surface(image)
    outline = mask.outline()
    outline_image = pygame.Surface(rect.size).convert_alpha()
    outline_image.fill((0, 0, 0, 0))
    for point in outline:
        outline_image.set_at(point, color)
        outline_image.set_at((point[0] + 1, point[1]), color)
        outline_image.set_at((point[0] + 2, point[1]), color)
    return outline_image.convert_alpha()


def str_to_seed(string: str) -> int:
    """Creates valid seed value from string."""
    str_sum = 0
    for char in string:
        str_sum += ord(char)
    return str_sum
