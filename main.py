from modules.position import *
from modules import settings
from modules import events
from modules import saves
from modules import audio
from modules import calc

import pygame
import random
import sys
import os

os.system("cls || clear")


# System arguments.
for arg in sys.argv[1:]:
    if arg.startswith("@"):
        seed = arg.removeprefix("@")
        seed = int(seed) if seed.isnumeric() else calc.str_to_seed(seed)

        if saves.get_saved_seed() != seed:
            print(f"Using custom seed: {seed} (cleared previous save: {saves.get_saved_seed()})\n")
            saves.remove_save()
            
        else:
            print(f"Using custom seed: {seed} (same as in previous sesssion)\n")
            
        settings.SEED = seed

    if arg.lower() == "--no-save":
        settings.AVOID_SAVE = True
        print("Avoiding save:\n  * Not applying saved changes to world.",
              "  * Not saving future changes in this session.\n", sep="\n")

    if arg.lower() == "--clear-save":
        saves.remove_save()
        print("Cleared save. Clean world will be generated and \
              upcoming changes will be saved.\n")
        
    if arg.lower() in ("--help", "help", "h", "-h", "--h"):
        print("""
--- HELP --

Available startup options:
    --no-save:    Do not apply saved changes and don't save upcoming changes.
    --clear-save: Removes saved file.
    @SEED:        (Replace 'SEED' with an value) Sets custom seed for world. 
                  (Removes current save file.)
        
Game controls are displayed after startup.

(For ~10FPS boost use `pygame-ce` instead of `pygame` library.)
        """)

print("""
Controls:
  (Keyboard)
  WSAD : Move player.
  Space: Jump.
        
  (Mouse)
  Move cursor  : Highlights block.
  Scroll       : Selects block.
  Left button  : Destroy highlighted block.
  Right button : Places selected block on highlighted block.
  Middle button: Move player using PathFinding algorithm.
\n
""")

random.seed(settings.SEED)
saves.init()
pygame.init()
pygame.event.set_allowed([
    pygame.QUIT,
    pygame.KEYDOWN,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEWHEEL
])
screen = pygame.display.set_mode(
    (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
)
screen.set_alpha(None)


from modules import weather
from modules import player
from modules import world


w = world.World()
p = player.Player(screen, w)
p.render()
weather.start_weather_thread()
clock = pygame.time.Clock()


while 1:
    clock.tick()
    mx, my = pygame.mouse.get_pos()

    events.EventLoop.execute_all_loops()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                p.move(AngleDirection.W, True)

            if event.key == pygame.K_d:
                p.move(AngleDirection.E, True)

            if event.key == pygame.K_w:
                p.move(AngleDirection.N, True)

            if event.key == pygame.K_s:
                p.move(AngleDirection.S, True)

            if event.key == pygame.K_SPACE:
                p.start_jump()

        if event.type == pygame.MOUSEBUTTONDOWN:

            # Left click
            if pygame.mouse.get_pressed()[0]:
                h_block = w.get_highlighted_block(mx, my)
                if h_block:
                    w.set_at(h_block.block.coordinate, None)
                    audio.play_sfx_break()
                    if h_block.block.coordinate == p.pos:
                        p.fall()

            # Middle click
            if pygame.mouse.get_pressed()[1]:
                h_block = w.get_highlighted_block(mx, my)
                if h_block:
                    p.pathfind_move(h_block.block.coordinate)

            # Right click
            if pygame.mouse.get_pressed()[2]:
                h_block = w.get_highlighted_block(mx, my)
                if not h_block:
                    continue

                block = h_block.block
                face = h_block.face

                if face == BlockFace.TOP:
                    new_coord = h_block.block.coordinate.add_z(1)

                if face == BlockFace.LEFT:
                    new_coord = h_block.block.coordinate.add_y(1)

                if face == BlockFace.RIGHT:
                    new_coord = h_block.block.coordinate.add_x(1)

                if new_coord != p.pos.add_z(1) and new_coord != p.pos.add_z(2):
                    if new_coord.z in range(settings.CHUNK_MAX_HEIGHT - 1):
                        w.set_at(
                            new_coord,
                            p.get_selected_block_class()(new_coord)
                        )
                        audio.play_sfx_put()

        if event.type == pygame.MOUSEWHEEL:
            p.update_picked_block(event.y)

    p.render()

    caption_fps = f"{round(clock.get_fps())} FPS"
    caption_pos = f"{p.pos.x}/{p.pos.y}/{p.pos.z}"
    caption_ch = f"{w.current_chunk.x}, {w.current_chunk.y}"
    pygame.display.set_caption(f"{caption_fps} | {caption_pos} ({caption_ch})")
