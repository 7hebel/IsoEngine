from modules import position
from modules import events
from modules import calc

from dataclasses import dataclass
import random
import pygame
import uuid


@dataclass
class Particle:
    pos: position.Coordinate
    texture: pygame.Surface

    def __post_init__(self) -> None:
        self._id = uuid.uuid4().hex
        self.render_x, self.render_y = calc.calc_tile_pos(
            self.pos.x, self.pos.y, self.pos.z
        )
        self.rect = self.texture.get_rect().move(self.render_x, self.render_y)


active_particles: list[Particle] = []


WATER_PARTICLE_TEXTURES = [
    pygame.image.load("./res/texture/particles/water/0.png").convert_alpha(),
    pygame.image.load("./res/texture/particles/water/1.png").convert_alpha(),
    pygame.image.load("./res/texture/particles/water/2.png").convert_alpha(),
    pygame.image.load("./res/texture/particles/water/3.png").convert_alpha(),
]


def create_water_particle(coord: position.Coordinate, sec: int = 1) -> None:
    """Creates and saves new particle that will be rendered and removed after sec seconds."""
    texture = random.choice(WATER_PARTICLE_TEXTURES)
    particle = Particle(coord.add_z(1), texture)
    active_particles.append(particle)

    events.main_loop.add_event(
        events.CallEvent(
            lambda: active_particles.remove(particle), events.in_n_seconds(sec)
        )
    )
