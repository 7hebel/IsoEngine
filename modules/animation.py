from modules import events

import pygame
import math


INIT_OFFSET = 20


class ChunkChangeAnimation:
    """Blocks fly-up effect on rendering new chunk based on their distance from player."""
    
    def __init__(self) -> None:
        self.enter_pos = (0, 0)
        self.progress = -1

    def update_rect(self, x: int, y: int, rect: pygame.Rect) -> pygame.Rect:
        """Move block's rect by it's progress distance."""
        if self.progress == -1:
            return rect

        distance = round(math.dist(self.enter_pos, (x, y)))
        new_y = INIT_OFFSET - self.progress + (distance * 10)

        if new_y <= 0:
            return rect

        r = rect.copy()
        r = r.move(0, new_y)
        return r

    def tick(self) -> None:
        self.progress += 10

        if self.progress < 50 * INIT_OFFSET:
            events.anim_loop.add_event(
                events.CallEvent(self.tick, events.in_n_seconds(0.01))
            )

    def reset(self, enter_position) -> None:
        """Reset animation's progress."""
        events.anim_loop.clear()
        self.progress = 0
        self.enter_pos = (enter_position.x, enter_position.y)
        self.tick()
