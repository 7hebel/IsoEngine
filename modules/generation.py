"""World generation using seeded randomness and Perlin noise."""

from modules import position
from modules import settings
from modules import voxels
from modules import saves
from modules import calc

from perlin_noise import PerlinNoise
import random


PERLIN_MIN = -0.5
PERLIN_MAX = 0.5


def normalize_noise(value: float) -> float:
    if value < PERLIN_MIN:
        value = PERLIN_MIN
    if value > PERLIN_MAX:
        value = PERLIN_MAX

    return round(value, 2)


height_noise = PerlinNoise(octaves=1.5, seed=settings.SEED)


def generate_chunk_noise(
    chunk_x: int, chunk_y: int, noise: PerlinNoise = height_noise
) -> list[list[float]]:
    """Generates 2D list of height values for individual chunk based on it's (X, Y)"""
    size = settings.CHUNK_SIZE

    perlin_map = [
        [
            normalize_noise(noise([y / size, x / size]))
            for x in range((size * chunk_x), (size * chunk_x + size))
        ]
        for y in range((size * chunk_y), (size * chunk_y + size))
    ]
    return perlin_map


WATER_HEIGHT = range(1, 3)
VOXELS_GENERATION_MAP = {
    range(0, 1): voxels.V_Stone,
    range(1, 3): voxels.V_Dirt,
    range(3, 12): voxels.V_Grass,
    range(12, settings.CHUNK_MAX_HEIGHT): None,
}


def generate_chunk(chunk_x: int, chunk_y: int) -> list[list[list[voxels.Voxel | None]]]:
    """Generates 3D array of voxels for specific chunk."""
    noise = generate_chunk_noise(chunk_x, chunk_y)

    min_height = 1
    max_height = settings.CHUNK_MAX_HEIGHT // 1.5

    voxels_map = []
    water_positions = []
    possible_unfilled_water: list[position.Coordinate] = []
    for z in range(settings.CHUNK_MAX_HEIGHT):
        voxels_y = []

        for y in range(settings.CHUNK_SIZE):
            voxels_x = []

            for x in range(settings.CHUNK_SIZE):
                highest = round(
                    calc.interpolation(
                        [PERLIN_MIN, min_height], [PERLIN_MAX, max_height], noise[y][x]
                    )
                )

                # Add enviroment objects.
                if z == highest + 1:
                    if random.randint(1, 35) == 1 and not isinstance(
                        voxels_map[z - 1][y][x], voxels.V_Water
                    ):
                        voxels_x.append(
                            voxels.random_env_object(position.Coordinate(x, y, z))
                        )
                        continue

                if z > highest:
                    if isinstance(voxels_map[z - 1][y][x], voxels.V_Water):
                        pos = position.Coordinate(x, y, z)
                        possible_unfilled_water.append(pos)

                    voxels_x.append(None)
                    continue

                voxel = None
                for z_range, voxel_type in VOXELS_GENERATION_MAP.items():
                    if z in z_range:
                        if voxel_type is None:
                            break
                        voxel = voxel_type(position.Coordinate(x, y, z))

                if highest in WATER_HEIGHT and z in WATER_HEIGHT:
                    pos = position.Coordinate(x, y, z)
                    voxel = voxels.V_Water(pos)
                    water_positions.append(pos)

                voxels_x.append(voxel)
            voxels_y.append(voxels_x)
        voxels_map.append(voxels_y)

    # Fill possibly unfilled water positions.
    for possible_pos in possible_unfilled_water:
        for bound_pos in calc.get_cross_bounding_pos(possible_pos).values():
            try:
                if isinstance(
                    voxels_map[bound_pos.z][bound_pos.y][bound_pos.x], voxels.V_Water
                ):
                    water_positions.append(possible_pos)
                    voxels_map[possible_pos.z][possible_pos.y][possible_pos.x] = (
                        voxels.V_Water(possible_pos)
                    )
                    break

            except IndexError:
                pass

    # Update water edges.
    for water_pos in water_positions:
        bound_angles = []

        top_pos = water_pos.add_z(1)
        if isinstance(voxels_map[top_pos.z][top_pos.y][top_pos.x], voxels.V_Water):
            continue

        for angle, pos in calc.get_cross_bounding_pos(water_pos).items():
            pos = pos.add_z(1)
            try:
                if voxels_map[pos.z][pos.y][pos.x] is not None:
                    bound_angles.append(angle)
            except IndexError:
                pass

        angle_name = position.combine_angles_str(bound_angles)
        new_texture = voxels.WATER_TEXTURES.get(angle_name)
        if new_texture:
            new_texture = new_texture.convert_alpha()
            voxels_map[water_pos.z][water_pos.y][water_pos.x].texture = new_texture

    # Apply difference from save.
    if saves.has_chunk(chunk_x, chunk_y):
        diff = saves.get_chunk(chunk_x, chunk_y)
        for raw_pos, voxel_name in diff.items():
            x, y, z = raw_pos.split(".")
            x, y, z = int(x), int(y), int(z)
            coords = position.Coordinate(x, y, z)
            voxel = voxels.Voxel.from_name(voxel_name, coords)
            voxels_map[z][y][x] = voxel

    return voxels_map
