from dataclasses import dataclass


@dataclass
class Coordinate:
    x: int
    y: int
    z: int

    def __hash__(self) -> int:
        return hash(f"{self.x}.{self.y}.{self.z}")

    def add_x(self, x_: int) -> "Coordinate":
        return Coordinate(self.x + x_, self.y, self.z)

    def add_y(self, y_: int) -> "Coordinate":
        return Coordinate(self.x, self.y + y_, self.z)

    def add_z(self, z_: int) -> "Coordinate":
        return Coordinate(self.x, self.y, self.z + z_)

    def get_sum(self) -> int:
        return self.x + self.y + self.z

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)


class BlockFace:
    NONE  = -1
    TOP   = 0
    LEFT  = 1
    RIGHT = 2


class AngleDirection:
    N  = 0
    NE = 45
    E  = 90
    SE = 135
    S  = 180
    SW = 225
    W  = 270
    NW = 315


NORTHISH = {AngleDirection.N, AngleDirection.NE, AngleDirection.NW}
SOUTHISH = {AngleDirection.S, AngleDirection.SE, AngleDirection.SW}
EASTISH  = {AngleDirection.E, AngleDirection.NE, AngleDirection.SE}
WESTISH  = {AngleDirection.W, AngleDirection.NW, AngleDirection.SW}


def combine_angles_str(angles: list[AngleDirection]) -> str:
    text = ""
    if AngleDirection.N in angles:
        text += "n"
    if AngleDirection.S in angles:
        text += "s"
    if AngleDirection.E in angles:
        text += "e"
    if AngleDirection.W in angles:
        text += "w"

    if text == "new" or text == "nsw":
        text = "nw"

    return text
