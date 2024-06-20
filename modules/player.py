from modules import particles
from modules import animation
from modules import position
from modules import cooldown
from modules import pathfind
from modules import settings
from modules import weather
from modules import events
from modules import voxels
from modules import world
from modules import calc

import pygame


class PreloadedTextures:
    def __init__(self) -> None:
        self.player_idle = {
            position.AngleDirection.N: pygame.image.load(
                "./res/texture/player/ne.png"
            ).convert_alpha(),
            position.AngleDirection.W: pygame.image.load(
                "./res/texture/player/nw.png"
            ).convert_alpha(),
            position.AngleDirection.E: pygame.image.load(
                "./res/texture/player/se.png"
            ).convert_alpha(),
            position.AngleDirection.S: pygame.image.load(
                "./res/texture/player/sw.png"
            ).convert_alpha(),
        }

        self.player_jump = {
            position.AngleDirection.N: pygame.image.load(
                "./res/texture/player/jump/ne.png"
            ).convert_alpha(),
            position.AngleDirection.W: pygame.image.load(
                "./res/texture/player/jump/nw.png"
            ).convert_alpha(),
            position.AngleDirection.E: pygame.image.load(
                "./res/texture/player/jump/se.png"
            ).convert_alpha(),
            position.AngleDirection.S: pygame.image.load(
                "./res/texture/player/jump/sw.png"
            ).convert_alpha(),
        }

        self.shadow_full_img = pygame.image.load(
            "./res/texture/shadow/shadow_full.png"
        ).convert_alpha()
        self.shadow_left_img = pygame.image.load(
            "./res/texture/shadow/shadow_left.png"
        ).convert_alpha()
        self.shadow_right_img = pygame.image.load(
            "./res/texture/shadow/shadow_right.png"
        ).convert_alpha()
        self.shadow_corner_img = pygame.image.load(
            "./res/texture/shadow/shadow_corner.png"
        ).convert_alpha()
        self.highlight_img = pygame.image.load(
            "./res/texture/highlight.png"
        ).convert_alpha()
        self.background_img = pygame.image.load(
            f"./res/texture/bg/{calc.calc_time_bg_index()}.png"
        ).convert_alpha()
        self.background_img = pygame.transform.scale(
            self.background_img, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        ).convert_alpha()
        self.pf_dest = pygame.image.load("./res/texture/pfdest.png").convert_alpha()

        self.pick_block_ui = []
        for voxel_type in voxels.ALL_VOXELS:
            texture = voxel_type(position.Coordinate(-1, -1, -1)).texture
            self.pick_block_ui.append(texture)


class Player:
    def __init__(self, screen: pygame.Surface, world: world.World):
        self.screen = screen
        self.pos = position.Coordinate(8, 8, 16)
        self.world = world
        self.facing = position.AngleDirection.S
        self.is_jumping = False
        self.chunk_load_anim = animation.ChunkChangeAnimation()
        self.preloaded_textures = PreloadedTextures()
        self.pick_block_index = 0
        self.pathfinder = None
        self.render_x, self.render_y, self.rect = None, None, None
        self.__recalc_render_data()
        self.fall()

    def __recalc_render_data(self):
        self.render_x, self.render_y = calc.calc_tile_pos(
            self.pos.x, self.pos.y, self.pos.z
        )
        self.rect = self.get_texture().get_rect().move(self.render_x, self.render_y)

    def get_real_pos(self) -> position.Coordinate:
        """Returns player's real position in the world (not relative to chunk)."""
        x_mult, y_mult = self.world.current_chunk.x, self.world.current_chunk.y
        return position.Coordinate(self.pos.x * x_mult, self.pos.y * y_mult, self.pos.z)

    def start_jump(self) -> None:
        if cooldown.jump_cooldown.is_on_cooldown():
            return
        if self.is_jumping:
            return
        if self.world.get_at_coord(self.pos.add_z(3)) is not None:
            return

        self.is_jumping = True
        cooldown.jump_cooldown.start_cooldown()
        self.pos = self.pos.add_z(2)
        self.__recalc_render_data()

        fall_ev = events.CallEvent(
            to_call=[self.end_jump], at_time=events.in_n_seconds(0.5)
        )
        events.main_loop.add_event(fall_ev)

    def end_jump(self) -> None:
        self.fall()
        self.is_jumping = False

    def update_picked_block(self, change: int) -> None:
        """Changes currently picked block in the UI."""
        new_value = self.pick_block_index + change
        max_value = len(self.preloaded_textures.pick_block_ui) - 1
        if new_value < 0:
            new_value = max_value + new_value + 1
        if new_value > max_value:
            new_value = max_value - new_value + 1
        self.pick_block_index = new_value

    def get_selected_block_class(self) -> voxels.Voxel:
        """Returns base class of selected voxel."""
        return voxels.ALL_VOXELS[self.pick_block_index]

    def get_texture(self) -> pygame.Surface:
        """Returns player's texture based on it's state."""
        if self.is_jumping:
            return self.preloaded_textures.player_jump.get(self.facing)
        return self.preloaded_textures.player_idle.get(self.facing)

    def pathfind_move(self, destination: position.Coordinate) -> None:
        """
        Move player to selected voxel using PathFinding algorithm.
        This movement can be interrupted with manual move.
        """
        self.pathfinder = None
        events.move_loop.clear()

        if destination == self.pos:
            self.pathfinder = None
            return

        self.pathfinder = pathfind.PathFinder(self.pos, destination, self.world)
        result_node = self.pathfinder.find()

        if result_node is None:
            self.pathfinder = None
            return

        moves = result_node.to_moves_sequence()
        if not moves:
            return

        wait = 0
        for direction, movetype in moves:
            wait += 1
            exec_time = 0.2 * wait

            if (
                movetype == pathfind.PF_MoveType.WALK
                or movetype == pathfind.PF_MoveType.FALL_WALK
            ):
                event = events.CallEvent(
                    [lambda d: self.move(d)],
                    events.in_n_seconds(exec_time),
                    [direction],
                )

            if movetype == pathfind.PF_MoveType.FALL_WALK:
                wait += 1

            if movetype == pathfind.PF_MoveType.JUMP_WALK:
                events.move_loop.add_event(
                    events.CallEvent(
                        [lambda: setattr(self, "pos", self.pos.add_z(2))],
                        events.in_n_seconds(exec_time),
                    )
                )
                event = events.CallEvent(
                    [lambda d: self.move(d)],
                    events.in_n_seconds(exec_time),
                    [direction],
                )

            events.move_loop.add_event(event)

        events.move_loop.add_event(
            events.CallEvent(
                [lambda: setattr(self, "pathfinder", None)],
                events.in_n_seconds(exec_time),
            )
        )

    def fall(self) -> None:
        """Fall to the nearest ground."""
        if self.pathfinder is not None:
            self.instant_fall()
            return

        new_coord = self.pos
        new_block = self.world.get_at_coord(new_coord)
        if new_block is None:
            new_coord = new_coord.add_z(-1)
            new_block = self.world.get_at_coord(new_coord)

            if new_coord.z <= 0 and new_block is None:
                self.pos = position.Coordinate(
                    settings.CHUNK_SIZE // 2,
                    settings.CHUNK_SIZE // 2,
                    settings.CHUNK_MAX_HEIGHT,
                )
                self.fall()
                return

            self.pos = new_coord
            self.__recalc_render_data()
            self.render()

            fall_ev = events.CallEvent(
                to_call=self.fall, at_time=events.in_n_seconds(0.05)
            )
            events.main_loop.add_event(fall_ev)

    def instant_fall(self) -> None:
        """Instantly drops player to the nearest ground without animation."""
        new_coord = self.pos
        new_block = self.world.get_at_coord(new_coord)
        while new_block is None:
            new_coord = new_coord.add_z(-1)
            new_block = self.world.get_at_coord(new_coord)

        self.pos = new_coord
        self.__recalc_render_data()
        self.render()

    def move(self, direction: position.AngleDirection, manual: bool = False) -> None:
        """Moves player in chosen direction."""
        if manual:
            self.pathfinder = None
            events.move_loop.clear()

        self.facing = direction

        if direction == position.AngleDirection.N:
            new_pos = self.pos.add_y(-1)
        if direction == position.AngleDirection.S:
            new_pos = self.pos.add_y(1)
        if direction == position.AngleDirection.E:
            new_pos = self.pos.add_x(1)
        if direction == position.AngleDirection.W:
            new_pos = self.pos.add_x(-1)

        face_level_coord = new_pos.add_z(2)
        if self.world.get_at_coord(face_level_coord) is not None:
            return

        nearest_higher_z = self.world.nearest_higher_at(new_pos.x, new_pos.y, new_pos.z)
        if nearest_higher_z == new_pos.z + 1:
            face_level_coord = new_pos.add_z(3)
            if self.world.get_at_coord(face_level_coord) is not None:
                return
            if self.world.get_at_coord(self.pos.add_z(3)) is not None:
                return
            new_pos = new_pos.add_z(1)

        # Change chunks
        if new_pos.x >= settings.CHUNK_SIZE:
            new_pos.x = new_pos.x - settings.CHUNK_SIZE
            self.world.update_current_chunk(1, 0)
            self.chunk_load_anim.reset(new_pos)
            if self.world.get_at_coord(new_pos) is not None:
                new_pos.z = self.world.highest_at(new_pos.x, new_pos.y) + 1
            self.pos = new_pos

        if new_pos.x < 0:
            new_pos.x = settings.CHUNK_SIZE - 1
            self.world.update_current_chunk(-1, 0)
            self.chunk_load_anim.reset(new_pos)
            if self.world.get_at_coord(new_pos) is not None:
                new_pos.z = self.world.highest_at(new_pos.x, new_pos.y) + 1
            self.pos = new_pos

        if new_pos.y >= settings.CHUNK_SIZE:
            new_pos.y = new_pos.y - settings.CHUNK_SIZE
            self.world.update_current_chunk(0, -1)
            self.chunk_load_anim.reset(new_pos)
            if self.world.get_at_coord(new_pos) is not None:
                new_pos.z = self.world.highest_at(new_pos.x, new_pos.y) + 1
            self.pos = new_pos

        if new_pos.y < 0:
            new_pos.y = settings.CHUNK_SIZE - 1
            self.world.update_current_chunk(0, 1)
            self.chunk_load_anim.reset(new_pos)
            if self.world.get_at_coord(new_pos) is not None:
                new_pos.z = self.world.highest_at(new_pos.x, new_pos.y) + 1
            self.pos = new_pos

        # Fall.
        new_ground_block = self.world.get_at_coord(new_pos)
        if new_ground_block is None and not self.is_jumping:
            self.pos = new_pos
            self.fall()
            return

        if new_ground_block:
            new_ground_block.on_stand(new_pos, self)

        self.pos = new_pos
        self.__recalc_render_data()

    def render(self):
        """Render entire scene."""
        mx, my = pygame.mouse.get_pos()
        self.screen.blit(self.preloaded_textures.background_img, (0, 0))
        player_drawed = False

        # Highlighted block.
        h_block = None
        if mx is not None and my is not None:
            h_block = self.world.get_highlighted_block(mx, my)

        # Clouds.
        for cloud in weather.render_clouds:
            rect = cloud.texture.get_rect()
            if rect.left < settings.SCREEN_WIDTH or rect.right > 0:
                self.screen.blit(cloud.texture, (cloud.screen_x, cloud.screen_y))

        # World.
        for z, z_row in enumerate(self.world.current_chunk.voxels):
            if z in self.world.current_chunk.skip_heights and self.pos.z != z:
                continue

            for y, row in enumerate(z_row):
                if calc.is_all_none(row) and self.pos.y != y:
                    continue

                for x, block in enumerate(row):
                    coordinate = position.Coordinate(x, y, z)

                    if block and not self.world.is_visible(block.coordinate):
                        continue

                    # Particles.
                    for particle in particles.active_particles:
                        if particle.pos == coordinate:
                            self.screen.blit(
                                particle.texture,
                                self.chunk_load_anim.update_rect(x, y, particle.rect),
                            )

                    if block is None:
                        if coordinate == self.pos:
                            self.screen.blit(self.get_texture(), self.rect)
                            player_drawed = True
                        continue

                    # Texture.
                    self.screen.blit(
                        block.texture,
                        self.chunk_load_anim.update_rect(x, y, block.rect),
                    )
                    if self.pos.z == z - 1 and (
                        x + 1 == self.pos.x or y + 1 == self.pos.y
                    ):
                        if block.rect.colliderect(self.rect):
                            inter = calc.rects_intersection(block.rect, self.rect)
                            chopped = pygame.transform.chop(
                                self.get_texture(), inter
                            ).convert_alpha()
                            self.screen.blit(chopped, self.rect)

                    # Shading.
                    is_block_above = (
                        self.world.get_at_coord(block.coordinate.add_z(1)) is not None
                    )
                    left_coord = block.coordinate.add_z(1).add_x(-1)
                    right_coord = block.coordinate.add_z(1).add_y(-1)
                    corner_coord = block.coordinate.add_z(1).add_x(-1).add_y(-1)

                    if not is_block_above:
                        # - Side shadows.
                        if self.world.get_at_coord(left_coord) is not None:
                            self.screen.blit(
                                self.preloaded_textures.shadow_left_img,
                                self.chunk_load_anim.update_rect(x, y, block.rect),
                            )

                        if self.world.get_at_coord(right_coord) is not None:
                            self.screen.blit(
                                self.preloaded_textures.shadow_right_img,
                                self.chunk_load_anim.update_rect(x, y, block.rect),
                            )

                        if self.world.get_at_coord(corner_coord) is not None:
                            self.screen.blit(
                                self.preloaded_textures.shadow_corner_img,
                                self.chunk_load_anim.update_rect(x, y, block.rect),
                            )

                        # - Full shadow.
                        z_dist = (
                            self.world.nearest_higher_at(
                                block.coordinate.x,
                                block.coordinate.y,
                                block.coordinate.z,
                            )
                            - block.coordinate.z
                        )
                        if z_dist in range(1, 11):
                            self.preloaded_textures.shadow_full_img.set_alpha(
                                255 * ((10 - z_dist) / 10)
                            )
                            self.screen.blit(
                                self.preloaded_textures.shadow_full_img,
                                self.chunk_load_anim.update_rect(x, y, block.rect),
                            )

                    # Player.
                    if coordinate == self.pos:
                        self.screen.blit(self.get_texture(), self.rect)
                        player_drawed = True

                    # Pathfind destination.
                    if self.pathfinder and coordinate == self.pathfinder.dest:
                        self.screen.blit(
                            self.preloaded_textures.pf_dest,
                            self.chunk_load_anim.update_rect(x, y, block.rect),
                        )

                    # Highlight.
                    if (
                        h_block
                        and h_block.block.coordinate.z == z
                        and h_block.block.coordinate.y == y
                        and h_block.block.coordinate.x == x
                    ):
                        outline_texture = calc.get_outline(h_block.block.texture)
                        self.screen.blit(
                            outline_texture,
                            self.chunk_load_anim.update_rect(x, y, block.rect),
                        )
                        if not isinstance(
                            h_block.block, voxels.SKIP_ON_VISIBLITY_CHECK
                        ):
                            self.screen.blit(
                                self.preloaded_textures.highlight_img,
                                self.chunk_load_anim.update_rect(x, y, block.rect),
                            )

        if not player_drawed:
            self.screen.blit(self.get_texture(), self.rect)

        # UI.
        for offset_x, block_texture in enumerate(self.preloaded_textures.pick_block_ui):
            rect = block_texture.get_rect().move((offset_x + 3.5) * 80, 20)
            self.screen.blit(block_texture, rect)
            if offset_x == self.pick_block_index:
                outline = calc.get_outline(block_texture, (250, 50, 50))
                self.screen.blit(outline, rect)

        pygame.display.flip()
