import pygame
import sys
from scripts.Utilities import load_images, Animation
from scripts.Tilemap import Tilemap

RENDER_SCALE = 2.0  # How much to upscale the low-res display for a pixel-art effect.

class Editor:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('editor')

        # Main window (scaled) and low-res display surface
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()

        self.movement = [False, False, False, False]  # [left, right, up, down] movement flags

        # Load all tile images grouped by type
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'spawners': load_images('tiles/spawners')
        }

        self.tilemap = Tilemap(self, tile_size=16)  # Tilemap to store and render tiles

        # Try to load an existing map file; ignore if missing
        try:
            self.tilemap.Load('data/maps/map.json')
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]  # Camera scroll offset in pixels

        # Tile selection state for the editor UI
        self.tile_list = list(self.assets)  # Names of tile categories
        self.tile_group = 0                 # Index of current category
        self.tile_variant = 0               # Index of tile variant in that category
        self.clicking = False               # Left mouse button is held
        self.right_clicking = False         # Right mouse button is held
        self.shift = False                  # Shift key is held (for variant selection)
        self.ongrid = True                  # Place tiles snapped to grid or freely

    def Run(self):
        # Main editor loop
        while True:
            self.display.fill((0, 0, 0))  # Clear display

            # Move camera based on WASD keys (movement flags)
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2  # right-left
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2  # down-up

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            self.tilemap.Render(self.display, offset=render_scroll)  # Draw visible tiles

            # Get current selected tile image and make it semi-transparent as a preview
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            # Mouse position adjusted for render scale and scroll
            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (
                int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size)
            )

            # Draw a ghost tile under the mouse cursor (grid-aligned or free)
            if self.ongrid:
                self.display.blit(
                    current_tile_img,
                    (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1])
                )
            else:
                self.display.blit(current_tile_img, mpos)

            # Place or erase tiles based on mouse buttons
            if self.clicking and self.ongrid:
                # Place tile in the grid dictionary
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {
                    'type': self.tile_list[self.tile_group],
                    'variant': self.tile_variant,
                    'pos': tile_pos
                }
            if self.right_clicking:
                # Remove tile from grid if it exists
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                # Also check and remove any off-grid decorations at mouse location
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(
                        tile['pos'][0] - self.scroll[0],
                        tile['pos'][1] - self.scroll[1],
                        tile_img.get_width(),
                        tile_img.get_height()
                    )
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            # Show currently selected tile preview in corner of screen
            self.display.blit(current_tile_img, (5, 5))

            # Handle events: quitting, placing/removing tiles, switching tiles, saving, autotiling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click: start placing tiles
                        self.clicking = True
                        if not self.ongrid:
                            # Place a freely positioned decoration
                            self.tilemap.offgrid_tiles.append({
                                'type': self.tile_list[self.tile_group],
                                'variant': self.tile_variant,
                                'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])
                            })
                    if event.button == 3:  # Right click: start erasing
                        self.right_clicking = True

                    # Scroll wheel switches variants or categories
                    if self.shift:  # Holding shift cycles variants within a category
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                    else:  # Without shift, cycle tile groups (categories)
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    # Movement keys for camera scrolling
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    # Toggle grid snapping
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    # Save current map to file
                    if event.key == pygame.K_o:
                        self.tilemap.Save('data/maps/map.json')
                    # Apply autotiling to smooth edges/corners
                    if event.key == pygame.K_t:
                        self.tilemap.AutoTile()
                    # Hold shift for variant selection
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True

                if event.type == pygame.KEYUP:
                    # Stop movement when key released
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

            # Upscale the low-res display surface and draw to the screen
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)  # Cap frame rate at 60 FPS

# Create and run the editor
editor = Editor()
editor.Run()