# --Imports--
import math
import random
import sys
import os

import pygame
from scripts.Clouds import Clouds
from scripts.Entities import Player, Enemy
from scripts.Particle import Particle
from scripts.Tilemap import Tilemap
from scripts.Utilities import Animation, load_image, load_images
from scripts.Spark import Spark


# -- Game class --
# creating game class, a game object to deal with image rendering, window running, user inputs etc
class Game:
    def __init__(self):

        pygame.init()

        pygame.display.set_caption("ninja game")

        """
        Creates a window and then a surface with 2x less resolution 
        The surface will be blitted to the display - we will blit images to the display
        Blitting images onto the display then scaling the display to match the screen is what creates the pixel art effect
        """
        self.screen = pygame.display.set_mode((640, 480))

        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        
        # self.display: the main rendering surface where entities and effects are drawn.
        # Using SRCALPHA enables per-pixel transparency for later mask operations.
        self.display_2 = pygame.Surface((320, 240))
       

        self.clock = pygame.time.Clock()
        self.movement = [False, False]

        """
        all the game assets, images that we will blit to the display:
        each key has a list (as its value) of image variants for use
        The animation class takes the list of image variants as a parameter for use 
        """
        # -- Game assets--

        self.assets = {
            # --Tile and entity graphics--
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "player": load_image("entities/player.png"),
            "background": load_image("background.png"),
            "clouds": load_images("clouds"),
            "gun": load_image('gun.png'),
            "projectile": load_image('projectile.png'),
            # --Player animations--
            "player/idle": Animation(
                load_images("entities/player/idle"), image_duration=6
            ),
            "player/run": Animation(
                load_images("entities/player/run"), image_duration=4
            ),
            "player/jump": Animation(load_images("entities/player/jump")),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/player/wall_slide")),
             # --Entity animations--
             "enemy/idle": Animation(
                load_images("entities/enemy/idle"), image_duration=6
            ),
            "enemy/run": Animation(
                load_images("entities/enemy/run"), image_duration=4
            ),
            # --Particle animations--
            "particle/leaf": Animation(
                load_images("particles/leaf"), image_duration=20, loop=False
            ),
            "particle/particle": Animation(
                load_images("particles/particle"), image_duration=6, loop=False
            )
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav')
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)


        self.clouds = Clouds(self.assets["clouds"], count=16)

        self.player = Player(self, (50, 50), (8, 15))

        # --Tilemap initialisation--
        self.tilemap = Tilemap(self, tile_size=16)

        # --Level data-
        self.level = 0
        self.Load_Level(self.level) # load the first level

        self.screenshake = 0 # Holds the current intensity of the screen shake effect (bigger number = more shake)

        

  
    # Load_Level method
    def Load_Level(self, map_id):
        """
        Loads a level by its map ID, populating all necessary game objects
        like the player’s position, enemies, and particle spawners.
        """
        # Load tilemap data from a JSON file.
        self.tilemap.Load('data/maps/' + str(map_id) + '.json')

        # Create "leaf spawner" areas by extracting specific tree tiles.
        # These spawn falling leaf particles during gameplay.
        self.leaf_spawners = []
        for tree in self.tilemap.Extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(
                pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13)
            )

        # ENEMY AND PLAYER SPAWNING
        self.enemies = []
        for spawner in self.tilemap.Extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                # Variant 0 = player start location.
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                # Variant 1 = enemy spawner, so add an Enemy instance.
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        # Initialize empty lists for all projectiles, particles, and sparks.
        self.projectiles = []  # Holds active bullets fired by enemies.
        self.particles = []    # Holds decorative particles (e.g., leaves).
        self.sparks = []       # Holds spark effects for shooting and destruction.

        # Camera scroll position and death timer reset.
        self.scroll = [0, 0]
        self.dead = 0 

        self.transition = -30
        # Controls the level transition animation.
        # Negative values mean the screen is "covered" (start of the transition),
        # positive values represent uncovering the screen (end of the transition).

    # this is the main game function where we do things while the game is running such as listening to inputs
    def Run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        # --Main loop--
        while True:
            self.display.fill((255, 255, 255, 0))
            # Clear the main display every frame by filling it with transparent black.
            # This ensures old drawings don't persist between frames.

            self.display_2.blit(self.assets["background"], (0, 0))
            # Start by drawing the background image onto display_2 before adding outlines
            # and the main display contents.

            self.screenshake = max(0, self.screenshake - 1)
            # Each frame, reduce the screenshake intensity by 1.
            # `max(0, …)` prevents it from going below 0, so the effect stops smoothly

            if not len(self.enemies):  
                # If there are no enemies left in the level...
                self.transition += 1  
                # ...increment the transition counter each frame (start revealing the next level).
                if self.transition > 30:
                    # When transition passes 30 (fully uncovered),
                    # move to the next level (but don't exceed the number of maps available).
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.Load_Level(self.level)

            if self.transition < 0:
                self.transition += 1  
                # If transition is still negative (initial "covered" state), increment toward 0.
                # This gradually uncovers the current level when it first loads.

            
            # Handle death timer: if the player died, increment a counter,
            # and reload the level after a short delay.
            if self.dead:
                self.dead += 1  
                # Start counting frames since the player died.
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)  
                    # After 10 frames, begin increasing `transition` to cover the screen again.
                if self.dead > 40:
                    self.Load_Level(self.level)  
                    # After 40 frames, reload the current level.

            """
            self.scroll represents the camera's position in the game world.
            If self.scroll = (0,0), the camera shows the world starting at (0,0) in the top-left of the screen.
            If we set self.scroll = player_x, player_y (without adjustment), the player will appear stuck
            at the top-left corner of the screen because the camera aligns its top-left with the player's position.
            To center the player on the screen, we subtract half the screen dimensions:
            desired_scroll = player_x - (screen_width / 2), player_y - (screen_height / 2)
            This offsets the camera so the player stays in the middle instead of the corner.
            Dividing everything by 30 acts as a lerping effect, where the scroll approaches (but never reaches) the desired position (self.player.Rect().centerx)
            All objects are stored in *world coordinates* (e.g. player at (500, 300)).
            The camera (self.scroll) defines which part of the world is visible on screen.
            When drawing, we subtract self.scroll to convert from world coords → screen coords:
            screen_x = world_x - scroll_x, screen_y = world_y - scroll_y
            Example:
            player world pos = (500, 300)
            camera scroll    = (400, 200)
            drawn on screen  = (100, 100)   <-- relative to the camera view
            Without subtracting self.scroll, objects would always be drawn at their world position,
            meaning the player would only ever appear when the camera is looking at the origin.
            Subtracting scroll makes the whole world shift as the camera moves, creating the scrolling effect.
            """
            self.scroll[0] += (
                self.player.Rect().centerx
                - self.display.get_width() / 2
                - self.scroll[0]
            ) / 30
            self.scroll[1] += (
                self.player.Rect().centery
                - self.display.get_height() / 2
                - self.scroll[1]
            ) / 30
            render_scroll = (
                int(self.scroll[0]),
                int(self.scroll[1]),
            )  # converting to an integer to avoid floating point errors

            # Iterate through each leaf spawner area to randomly generate leaf particles.
            for rect in self.leaf_spawners:
                # Equation for probability of spawning leaves. It is proportional to the spawner's area, larger area = higher spawn chance
                if random.random() * 49999 < rect.width * rect.height:
                    # Pick a random position within the bounds of spawner rectangle.
                    pos = (
                        rect.x + random.random() * rect.width,
                        rect.y + random.random() * rect.height,
                    )
                    # Create and store a new leaf particle with initial velocity and a random animation frame.
                    self.particles.append(
                        Particle(
                            self,
                            "leaf",
                            pos,
                            velocity=[-0.1, 0.3],
                            frame=random.randint(0, 20),
                        )
                    )

            """
            Each Render method renders an image onto the display by using render_scroll to convert its world coords → screen coords
            render_scroll acts as an 'offset' to the camera
            """

            self.clouds.Update()
            self.clouds.Render(self.display, offset=render_scroll)

            self.tilemap.Render(self.display, offset=render_scroll)

            # ENEMY UPDATES AND RENDERING
            for enemy in self.enemies.copy():
                kill = enemy.Update(self.tilemap, (0, 0))  # Update AI behavior and movement.
                enemy.Render(self.display, offset=render_scroll)  # Draw the enemy.
                if kill:
                    # If Update() returns True, the enemy was destroyed (e.g., by dash collision).
                    self.enemies.remove(enemy)


            # PLAYER UPDATE AND RENDERING
            if not self.dead: # If the player is still alive 
                # Update player position and animation based on movement input.
                self.player.Update(self.tilemap, ((self.movement[1] - self.movement[0]) * 2, 0))
                self.player.Render(self.display, offset=render_scroll)

            # PROJECTILE HANDLING
            for projectile in self.projectiles.copy():
                # projectile = [position[x,y], x_velocity, lifetime_counter]

                # Move projectile horizontally.
                projectile[0][0] += projectile[1]
                # Increase lifetime counter each frame.
                projectile[2] += 1

                # Draw the projectile at its current position, centered on its image.
                image = self.assets['projectile']
                self.display.blit(
                    image,
                    (
                        projectile[0][0] - image.get_width() / 2 - render_scroll[0],
                        projectile[0][1] - image.get_height() / 2 - render_scroll[1]
                    )
                )

                # --COLLISION CHECKS--
                # If the projectile hits a solid tile:
                if self.tilemap.Solid_Check(projectile[0]):
                    self.projectiles.remove(projectile)
                    # Create small sparks to indicate a bullet impact.
                    for _ in range(4):
                        self.sparks.append(
                            Spark(
                                projectile[0],
                                random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0),
                                2 + random.random()
                            )
                        )
                # If projectile has existed too long, remove it.
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                # If player is not dashing (dash < 50), check for hits.
                elif abs(self.player.dashing) < 50:
                    if self.player.Rect().collidepoint(projectile[0]):
                        # Projectile hit the player → trigger death sequence.
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.screenshake = max(16, self.screenshake)
                        # When hit by a projectile, ensure the screenshake is at least 16.
                        # If multiple hits occur in quick succession, this prevents tiny shakes from being overridden.
                        self.sfx['hit'].play()

                        #--Create an explosion of sparks and particles at the player's position.--
                        for _ in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.Rect().center, angle, 2 + random.random()))
                            self.particles.append(
                                Particle(
                                    self,
                                    'particle',
                                    self.player.Rect().center,
                                    velocity=[
                                        math.cos(angle + math.pi) * speed * 0.5,
                                        math.sin(angle + math.pi) * speed * 0.5
                                    ],
                                    frame=random.randint(0, 7)
                                )
                            )
                

            for spark in self.sparks.copy():
                # Move the spark according to its velocity and reduce its speed.
                kill = spark.Update()
                # Draw the spark polygon.
                spark.Render(self.display, offset=render_scroll)
                # If the spark has slowed to zero, remove it.
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            # Convert all non-transparent pixels on self.display into a binary mask.
            # Pixels with alpha > 0 become "1" (filled), and fully transparent pixels are ignored.

            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            # Convert the mask back into a surface:
            #   - setcolor is the color of filled mask pixels → semi-transparent black (alpha=180).
            #   - unsetcolor is the color for empty mask pixels → fully transparent.
            # This creates a silhouette of all visible objects on self.display.

            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                # Loop over four directions: left, right, up, down.
                # These small offsets create copies of the silhouette slightly shifted in each direction.
                self.display_2.blit(display_silhouette, offset)
                # Blit (draw) the shifted silhouettes onto display_2.
                # Overlapping these shifted silhouettes around the original shapes creates a "thickened"
                # border effect—an outline around the objects.
            

            # Update and render all particles.
            for particle in self.particles.copy():
                kill = (
                    particle.Update()
                )  # Update particle position and animation and check if it should be removed.
                particle.Render(
                    self.display, offset=render_scroll
                )  # Draw the particle to the screen.
                if particle.type == "leaf":
                    # Add a horizontal sin-like motion to simulate leaves drifting side to side. Makes the motion feel less robotic
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(
                        particle
                    )  # Remove the particle if its animation is finished.

            # --Pygame events--
            for (event) in (pygame.event.get()):  # waits for user input, run every loop to avoid windows shutting the game down (windows shuts down if no inputs are being waited for)
                if event.type == pygame.QUIT:
                    pygame.quit
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True  # or 1
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        if self.player.Jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_x:
                        self.player.Dash()
                    if event.key == pygame.K_f:
                        self.player.Parry()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False  # or 0
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            if self.transition:
                transition_surface = pygame.Surface(self.display.get_size())  # Create a surface the same size as the display to draw the transition effect.
                pygame.draw.circle(
                    transition_surface,
                    (255, 255, 255),
                    (self.display.get_width() // 2, self.display.get_height() // 2),  
                    # Draw the circle centered on the screen.
                    (30 - abs(self.transition)) * 8  
                    # Radius calculation:
                    #   - abs(self.transition) shrinks as transition moves toward 0,
                    #     so the radius grows or shrinks depending on entering/exiting a level.
                    #   - (30 - abs(self.transition)) * 8 → converts this value to pixels.
                )

                transition_surface.set_colorkey((255, 255, 255))  
                # Make white transparent so only the non-white parts show.

                self.display.blit(transition_surface, (0, 0))  
                # Blit (draw) the transition surface onto the display.
                # As transition moves, the circle shrinks or expands, creating a "wipe" effect:
                #   - Negative to zero: the circle grows, revealing the level.
                #   - Zero to positive: the circle shrinks, covering the screen for the next level or reload.

     
            self.display_2.blit(self.display, (0, 0))
            
            # Finally, draw the original, unmodified main display (self.display) on top of display_2.
            # At this point:
            #   - display_2 contains the background and the outlines.
            #   - self.display contains the original objects.
            # By layering the two, the objects are outlined by the shifted silhouettes,
            # producing a glowing or highlighted effect without altering the actual sprites.

            screenshake_offset = (
            random.random() * self.screenshake - self.screenshake / 2,  
            # Horizontal offset:
            #   random.random() * self.screenshake → value between 0 and `screenshake`.
            #   Subtracting `screenshake / 2` recenters it so the range becomes (-screenshake/2, +screenshake/2).
            #   This ensures equal jitter in both left and right directions.

            random.random() * self.screenshake - self.screenshake / 2  
            # Vertical offset:
            #   Same calculation as horizontal, giving a random vertical jitter.
            )

            # --- APPLYING THE OFFSET TO CREATE THE SHAKE ---
            self.screen.blit(
                pygame.transform.scale(self.display_2, self.screen.get_size()),  # Scale display to match screen resolution.
                screenshake_offset  # Draw (blit) the display with a small random offset to simulate shaking.
            )
            # As `self.screenshake` decreases over frames, the random offset becomes smaller.
            # This creates a strong initial jolt that fades out, acting as an impact
            pygame.display.update()  # refreshes the window, this creates a motion effect as things are drawn in different positions each loop
            self.clock.tick(60)


game = Game()
game.Run()
