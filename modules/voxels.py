from modules import particles
from modules import position
from modules import calc

import pygame
import random


TEXTURES_PATH = "./res/texture/"


DIRT_TEXTURES = []
for i in range(10):
    DIRT_TEXTURES.append(
        pygame.image.load(TEXTURES_PATH + f"dirt/{i}.png").convert_alpha()
    )

FLOWERS_TEXTURES = []
for i in range(7):
    FLOWERS_TEXTURES.append(
        pygame.image.load(TEXTURES_PATH + f"flowers/{i}.png").convert_alpha()
    )

GRASS_TEXTURES = []
for i in range(10):
    GRASS_TEXTURES.append(
        pygame.image.load(TEXTURES_PATH + f"grass/{i}.png").convert_alpha()
    )

ROCKS_TEXTURES = []
for i in range(5):
    ROCKS_TEXTURES.append(
        pygame.image.load(TEXTURES_PATH + f"rocks/{i}.png").convert_alpha()
    )

WOOD_TEXTURES = []
for i in range(5):
    WOOD_TEXTURES.append(
        pygame.image.load(TEXTURES_PATH + f"wood/{i}.png").convert_alpha()
    )

STONE_TEXTURES = []
for i in range(2):
    STONE_TEXTURES.append(
        pygame.image.load(TEXTURES_PATH + f"stone/{i}.png").convert_alpha()
    )

WATER_TEXTURES = {
    "full": pygame.image.load(TEXTURES_PATH + "water/full.png").convert_alpha(),
    "e": pygame.image.load(TEXTURES_PATH + "water/e.png").convert_alpha(),
    "n": pygame.image.load(TEXTURES_PATH + "water/n.png").convert_alpha(),
    "ne": pygame.image.load(TEXTURES_PATH + "water/ne.png").convert_alpha(),
    "nsew": pygame.image.load(TEXTURES_PATH + "water/nsew.png").convert_alpha(),
    "nw": pygame.image.load(TEXTURES_PATH + "water/nw.png").convert_alpha(),
    "s": pygame.image.load(TEXTURES_PATH + "water/s.png").convert_alpha(),
    "se": pygame.image.load(TEXTURES_PATH + "water/se.png").convert_alpha(),
    "sw": pygame.image.load(TEXTURES_PATH + "water/sw.png").convert_alpha(),
    "w": pygame.image.load(TEXTURES_PATH + "water/w.png").convert_alpha(),
}


class Voxel:
    def __init__(
        self, name: str, coordinate: position.Coordinate, texture: pygame.Surface
    ):
        self.name = name
        self.coordinate = coordinate
        self.texture = texture
        self.render_x, self.render_y = calc.calc_tile_pos(
            self.coordinate.x, self.coordinate.y, self.coordinate.z
        )
        self.rect = self.texture.get_rect().move(self.render_x, self.render_y)
        self.individual_value = None

    def on_stand(self, position, player) -> None:
        return

    @staticmethod
    def from_name(name: str, coords: position.Coordinate) -> "Voxel":
        if name is None:
            return None

        translation = {
            "desk": V_Desk,
            "grass": V_Grass,
            "dirt": V_Dirt,
            "flower": V_Flower,
            "rock": V_Rocks,
            "stone": V_Stone,
            "wood": V_Wood,
            "water": V_Water,
        }

        return translation.get(name)(coords)


class V_Desk(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__(
            "desk",
            coordinate,
            pygame.image.load(TEXTURES_PATH + "desk.png").convert_alpha(),
        )


class V_Grass(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__("grass", coordinate, random.choice(GRASS_TEXTURES))


class V_Dirt(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__("dirt", coordinate, random.choice(DIRT_TEXTURES))


class V_Flower(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__("flower", coordinate, random.choice(FLOWERS_TEXTURES))


class V_Rocks(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__("rock", coordinate, random.choice(ROCKS_TEXTURES))


class V_Stone(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__("stone", coordinate, random.choice(STONE_TEXTURES))


class V_Wood(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__("wood", coordinate, random.choice(WOOD_TEXTURES))


class V_Water(Voxel):
    def __init__(self, coordinate: position.Coordinate):
        super().__init__(
            "water", coordinate, WATER_TEXTURES.get("full").convert_alpha()
        )

    def on_stand(self, position, player) -> None:
        particles.create_water_particle(position)


ENVIRONMENT_OBJECTS = [V_Flower, V_Rocks, V_Wood]


def random_env_object(coordinate: position.Coordinate) -> Voxel:
    return random.choice(ENVIRONMENT_OBJECTS)(coordinate)


SKIP_ON_VISIBLITY_CHECK = (*ENVIRONMENT_OBJECTS, V_Water)
ALL_VOXELS = [V_Desk, V_Dirt, V_Flower, V_Grass, V_Rocks, V_Stone, V_Water, V_Wood]
