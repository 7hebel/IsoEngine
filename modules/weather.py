from modules import settings

from threading import Thread
import pygame
import random
import time


CLOUD_TEXTURES: list[pygame.Surface] = []
for i in range(7):
    CLOUD_TEXTURES.append(
        pygame.image.load(f"./res/texture/cloud/{i}.png").convert_alpha()
    )


class Cloud:
    def __init__(self):
        self.screen_x = 0
        self.screen_y = 0
        self.speed = random.randint(1, 3)
        self.texture = random.choice(CLOUD_TEXTURES)
        self.texture.set_alpha(random.randint(130, 200))
        self.texture = pygame.transform.scale_by(
            self.texture, random.randint(2, 5)
        ).convert_alpha()
        self.__random_init_pos()

        render_clouds.append(self)

    def __random_init_pos(self) -> None:
        min_y, max_y = -80, settings.SCREEN_HEIGHT + 80
        self.screen_x = settings.SCREEN_WIDTH + random.randint(50, 200)
        self.screen_y = random.randint(min_y, max_y)

    def move(self) -> None:
        self.screen_x -= self.speed
        if self.screen_x < -500:
            render_clouds.remove(self)


render_clouds: list[Cloud] = []


def start_weather_thread():
    def weather_worker():
        while 1:
            if random.randint(1, 150) == 2:
                Cloud()

            for cloud in render_clouds:
                cloud.move()
            time.sleep(1 / 40)

    worker = Thread(target=weather_worker, daemon=True)
    worker.start()
