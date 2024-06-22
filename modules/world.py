from modules import generation
from modules import position
from modules import settings
from modules import voxels
from modules import saves
from modules import calc

from dataclasses import dataclass
import random


@dataclass
class HighlightedItem:
    block: voxels.Voxel
    face: position.BlockFace


class Chunk:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.size = settings.CHUNK_SIZE

        self.voxels = generation.generate_chunk(self.x, self.y)
        self.skip_heights = []
        self.__calc_skip_heights()

    def __calc_skip_heights(self) -> None:
        skip = []
        for z, z_row in enumerate(self.voxels):
            if calc.is_all_none(z_row):
                skip.append(z)
                break

        self.skip_heights = skip

    def set_at(
        self, coordinate: position.Coordinate, item: voxels.Voxel | None
    ) -> bool:
        if coordinate.z > settings.CHUNK_MAX_HEIGHT - 1:
            return False
        z_row = self.voxels[coordinate.z]
        if coordinate.y > len(z_row) - 1:
            return False
        y_row = z_row[coordinate.y]
        if coordinate.x > len(y_row) - 1:
            return False

        self.voxels[coordinate.z][coordinate.y][coordinate.x] = item
        self.__calc_skip_heights()
        return True


class World:
    def __init__(self, seed: int = 10) -> None:
        self.seed = seed
        random.seed(seed)

        self.chunks: dict[tuple[int, int] : Chunk] = {(0, 0): Chunk(0, 0)}
        self.current_chunk: Chunk = self.chunks.get((0, 0))

        self.__load_bounding_chunks()

    def __load_chunk(self, x: int, y: int) -> None:
        pos = (x, y)
        if pos not in self.chunks:
            self.chunks[pos] = Chunk(x, y)

    def __load_bounding_chunks(self) -> None:
        for bounding_x, bounding_y in calc.get_bounding_chunks_pos(
            self.current_chunk.x, self.current_chunk.y
        ):
            self.__load_chunk(bounding_x, bounding_y)

    def update_current_chunk(self, change_x: int, change_y: int) -> bool:
        new_x = self.current_chunk.x + change_x
        new_y = self.current_chunk.y + change_y

        pos = (new_x, new_y)
        if pos not in self.chunks:
            self.__load_chunk(new_x, new_y)

        self.current_chunk = self.chunks.get(pos)
        self.__load_bounding_chunks()
        return True

    def get_at(self, x: int, y: int, z: int) -> voxels.Voxel | None:
        if x < 0 or y < 0 or z < 0:
            return None
        try:
            return self.current_chunk.voxels[z][y][x]
        except IndexError:
            return None

    def get_at_coord(self, coordinate: position.Coordinate) -> voxels.Voxel | None:
        return self.get_at(coordinate.x, coordinate.y, coordinate.z)

    def is_coord_valid(self, coordinate: position.Coordinate) -> bool:
        """Check if coordinate is inside chunk."""
        return not (
            coordinate.x < 0 or 
            coordinate.x > settings.CHUNK_SIZE or
            coordinate.y < 0 or
            coordinate.y > settings.CHUNK_SIZE or
            coordinate.z < 0
        )

    def set_at(
        self, coordinate: position.Coordinate, item: voxels.Voxel | None
    ) -> bool:
        """Puts item at given coordinate. Returns False is coord out of range."""
        saves.update(self.current_chunk, coordinate, item)
        status = self.current_chunk.set_at(coordinate, item)
        
        for coord in [coordinate, *calc.get_cross_bounding_pos(coordinate).values(), *calc.get_cross_bounding_pos(coordinate.add_z(-1)).values(), *calc.get_cross_bounding_pos(coordinate.add_z(1)).values()]:
            if self.is_coord_valid(coord) and isinstance(self.get_at_coord(coord), voxels.V_Water):
                self.update_water_shore(coord)
                
        return status

    def highest_at(self, x: int, y: int) -> int | None:
        """Highest block's Z index for (X, Y). (Not counting None)"""
        coord = position.Coordinate(x, y, settings.CHUNK_MAX_HEIGHT)
        for i in range(settings.CHUNK_MAX_HEIGHT - 1):
            coord = coord.add_z(-1)
            if self.get_at_coord(coord) is not None:
                return coord.z
        return None

    def nearest_higher_at(self, x: int, y: int, start_z: int) -> int:
        """Nearest higher Z index for (X, Y)."""
        coord = position.Coordinate(x, y, start_z)
        for _ in range((settings.CHUNK_MAX_HEIGHT - 1) - start_z):
            coord = coord.add_z(1)
            if self.get_at_coord(coord) is not None:
                return coord.z
        return 0

    def nearest_higher_ground_at(self, x: int, y: int, start_z: int) -> int:
        """Nearest higher Z index for (X, Y) that has None above."""
        z = start_z
        while z < settings.CHUNK_MAX_HEIGHT - 1:
            pos = position.Coordinate(x, y, z)
            if (
                self.get_at_coord(pos) is not None
                and self.get_at_coord(pos.add_z(1)) is None
                and self.get_at_coord(pos.add_z(2)) is None
            ):
                return z
            z += 1

        return start_z

    def nearest_lower_ground_at(self, x: int, y: int, start_z: int) -> int:
        """Nearest lower Z index for (X, Y) that has None above."""
        z = start_z
        while z >= 0:
            pos = position.Coordinate(x, y, z)
            if (
                self.get_at_coord(pos) is not None
                and self.get_at_coord(pos.add_z(1)) is None
                and self.get_at_coord(pos.add_z(2)) is None
            ):
                return z
            z -= 1

        return start_z

    def reachable_grounds_at(self, x: int, y: int) -> list[position.Coordinate]:
        """Find all reachable grounds at given (X, Y). (min 2 voxels of Z space.)"""
        reachable = []
        coord = position.Coordinate(x, y, 0)
        while coord.z < settings.CHUNK_MAX_HEIGHT - 2:
            if (
                self.get_at_coord(coord) is not None
                and self.get_at_coord(coord.add_z(1)) is None
                and self.get_at_coord(coord.add_z(2)) is None
            ):
                reachable.append(coord)
            coord = coord.add_z(1)
        return reachable

    def nearest_lower_at(self, x: int, y: int, start_z: int) -> int:
        """Nearest lower Z index for (X, Y)."""
        coord = position.Coordinate(x, y, start_z)
        for _ in range(start_z, -1, -1):
            coord = coord.add_z(-1)
            if self.get_at_coord(coord) is not None:
                return coord.z
        return 0

    def get_highlighted_block(self, mx: int, my: int) -> HighlightedItem | None:
        """Returns nearest highlighted block according to mouse x and y pos."""
        highlighted_block = None

        for z, z_row in enumerate(self.current_chunk.voxels):
            if z in self.current_chunk.skip_heights:
                continue

            for row in z_row:
                if calc.is_all_none(row):
                    continue

                for block in row:
                    if block and calc.is_in_real_rect(mx, my, block.rect):
                        highlighted_block = block

        if highlighted_block is None:
            return None

        face = calc.calc_block_face(mx, my, highlighted_block.rect)
        return HighlightedItem(block=highlighted_block, face=face)

    def is_visible(self, coords: position.Coordinate) -> bool:
        """Check if item is surrounded by other blocks from: TOP, LEFT, RIGHT."""
        top = self.get_at_coord(coords.add_z(1))
        left = self.get_at_coord(coords.add_y(1))
        right = self.get_at_coord(coords.add_x(1))

        for surrounding_block in [top, left, right]:
            if surrounding_block is None or isinstance(
                surrounding_block, voxels.SKIP_ON_VISIBLITY_CHECK
            ):
                return True
        return False

    def update_water_shore(self, coords: position.Coordinate) -> None:
        """Update water's texture according to it's bouding blocks."""
        bound_angles = []

        top_pos = coords.add_z(1)
        if isinstance(self.current_chunk.voxels[top_pos.z][top_pos.y][top_pos.x], voxels.V_Water):
            return

        for angle, pos in calc.get_cross_bounding_pos(coords).items():
            pos = pos.add_z(1)
            try:
                if self.current_chunk.voxels[pos.z][pos.y][pos.x] is not None:
                    bound_angles.append(angle)
            except IndexError:
                pass

        angle_name = position.combine_angles_str(bound_angles)
        new_texture = voxels.WATER_TEXTURES.get(angle_name)
        if new_texture:
            new_texture = new_texture.convert_alpha()
            self.current_chunk.voxels[coords.z][coords.y][coords.x].texture = new_texture