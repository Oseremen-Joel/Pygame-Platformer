import pygame
import math
import random
from scripts.Particle import Particle
from scripts.Spark import Spark

class PhysicsEntity:
    def __init__(self, game, entity_type, pos, size):
       self.game = game
       self.type = entity_type
       self.pos = list(pos) # lists are used as their elements can be changed, unlike tuples
       self.size = size
       self.velocity = [0, 0]
       self.collisions = {'up': False, 'down': False, 'right': False, 'left': False} # used to check what direction an entity has collided with (in the current loop)

       self.action = ''
       self.anim_offset = (-3, -3) # offsets the entity's sprites and animations to avoid visual bugs like the player sinking into the ground
       self.flip = False # the way the entity is facing, right is false and left is true
       self.Set_Action('idle') # default action is always set to idle upon initialisation 

       self.last_movement = [0, 0] # the movement vector from the last frame, default to (0, 0) upon initialisation

    def Set_Action(self, action): # sets the entities action which changes their sprite accordingly
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].Copy()

    def Rect(self): # returns the rect of the entity, used for collisions
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def Update(self, tilemap, movement=(0, 0)): # updates the entity's position: including its position and collision states
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False} # refreshes the states
        # It's important to know that movement doesn't store a velocity vector but stores the player's input i.e. the direction they intended to move in
       
            # Combine the player's current movement with their current velocity
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        # --- Horizontal movement and collision (world coordinates) ---
        self.pos[0] += frame_movement[0]      # Move along the x axis 
        entity_rect = self.Rect()             # Get the updated hitbox for collision checks afetr movement
        for rect in tilemap.Physics_Rects_Around(self.pos):  # Check nearby solid tiles only
            if entity_rect.colliderect(rect):                # If colliding with a tile horizontally:
                if frame_movement[0] > 0:                    # Moving right -> Right side of the hixbox collides with the tile
                    entity_rect.right = rect.left             # Snap player to the left edge of the tile
                    self.collisions['right'] = True           # Record collision on right side
                if frame_movement[0] < 0:                    # Moving left -> Left side of the hixbox collides with the tile
                    entity_rect.left = rect.right             # Snap player to the right edge of the tile
                    self.collisions['left'] = True            # Record collision on left side
                self.pos[0] = entity_rect.x                   # Update x position after correction

        # --- Vertical movement and collision ---
        self.pos[1] += frame_movement[1]      # Move along the y axis
        entity_rect = self.Rect()             # Get the updated hitbox for collision checks after movement
        for rect in tilemap.Physics_Rects_Around(self.pos):  # Check nearby solid tiles only
            if entity_rect.colliderect(rect):                # If colliding with a tile vertically:
                if frame_movement[1] > 0:                    # Moving down -> down side of the hixbox collides with the tile
                    entity_rect.bottom = rect.top             # Snap to the top of the tile
                    self.collisions['down'] = True            # Record collision on the down side
                if frame_movement[1] < 0:                    # Moving up -> up side of the hitbox collides with the tile
                    entity_rect.top = rect.bottom             # Snap to the down side of the tile
                    self.collisions['up'] = True              # Record collision above
                self.pos[1] = entity_rect.y                   # Update y position after correction

        # Flip the sprite image based on horizontal input direction
        if movement[0] > 0:   # Moving right
            self.flip = False
        if movement[0] < 0:   # Moving left
            self.flip = True
        
        self.last_movement = movement # set the last movement attribute to the movement on this frame, this means the next frame will have a reference to the movement beforehand

        # Apply gravity: slowly increase downward velocity, capped at 5
        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        # If colliding vertically (ground or ceiling), reset vertical velocity to stop movement
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        # Update the animation to match the movement
        self.animation.Update()

    # Render the image to the display  
    def Render(self, surface, offset=(0, 0)):
        surface.blit(pygame.transform.flip(self.animation.Image(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Enemy(PhysicsEntity):
    """
    The Enemy class represents a basic AI-controlled enemy in the game.
    It inherits from PhysicsEntity to reuse collision detection, physics,
    and animation handling. This enemy can patrol, detect edges, reverse direction,
    shoot projectiles toward the player, and be destroyed when hit by the player's dash.
    """
    def __init__(self, game, pos, size):
        """
        Initialize the enemy.
        :param game: Reference to the main game object (used to access player, assets, etc.).
        :param pos: The starting (x, y) position of the enemy on the map.
        :param size: The size of the enemy's collision rectangle.
        """
        # Call the base PhysicsEntity constructor with the type 'enemy'.
        super().__init__(game, 'enemy', pos, size)

        # walking is a countdown timer for how long the enemy keeps walking.
        # When it reaches 0, the enemy can stop, shoot, or choose a new direction.
        self.walking = 0

    def Update(self, tilemap, movement=(0, 0)):
        """
        Update the enemy’s behavior for one frame.
        Handles patrolling, edge detection, shooting logic, and checking for collisions with the player’s dash.
        :param tilemap: Reference to the Tilemap for collision and edge detection.
        :param movement: The movement vector to apply this frame (usually starts at (0, 0)).
        :return: True if the enemy is destroyed (so the game loop removes it), otherwise None.
        """
        # If currently walking (patrolling)
        if self.walking:
            # Look ahead: check for ground in front of the enemy to avoid falling off platforms.
            check_pos = (self.Rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)
            if tilemap.Solid_Check(check_pos):
                # If there’s a collision with a wall (left or right), flip direction.
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    # Otherwise, continue moving left or right depending on flip.
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                # If no ground is found ahead, reverse direction to stay on the platform.
                self.flip = not self.flip

            # Decrease walking countdown timer each frame.
            self.walking = max(0, self.walking - 1)

            # If the enemy has stopped walking, check if the player is in line of fire.
            if not self.walking:
                # Calculate vector from enemy to player.
                distance = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                # Only consider shooting if the player is close vertically.
                if abs(distance[1]) < 16:
                    # If facing left (flip=True) and player is to the left, shoot.
                    self.game.sfx['shoot'].play()
                    if (self.flip and distance[0] < 0):
                        
                        # Spawn a projectile moving left (-1.5 speed).
                        self.game.projectiles.append([[self.Rect().centerx - 7, self.Rect().centery], -1.5, 0])
                        # Create a small burst of sparks to simulate a muzzle flash.
                        for _ in range(4):
                            self.game.sparks.append(
                                Spark(self.game.projectiles[-1][0],
                                      random.random() - 0.5 + math.pi,
                                      2 + random.random()))
                    # If facing right (flip=False) and player is to the right, shoot.
                    if not self.flip and distance[0] > 0:
                        self.game.projectiles.append([[self.Rect().centerx + 7, self.Rect().centery], 1.5, 0])
                        for _ in range(4):
                            self.game.sparks.append(
                                Spark(self.game.projectiles[-1][0],
                                      random.random() - 0.5,
                                      2 + random.random()))
        # If not currently walking, randomly decide to start walking (idle behavior).
        elif random.random() < 0.01:
            # walking is set to a random duration, making movement unpredictable.
            self.walking = random.randint(30, 120)

        # Call the PhysicsEntity update to handle collisions, gravity, and animations.
        super().Update(tilemap, movement=movement)

        # Set animation based on horizontal movement.
        # If movement.x != 0, switch to 'run' animation; otherwise, use 'idle'.
        if movement[0] != 0:
            self.Set_Action('run')
        else:
            self.Set_Action('idle')

        # Check if the player is currently dashing at high speed.
        if abs(self.game.player.dashing) >= 50:
            # If the enemy’s rectangle overlaps with the player’s rectangle during a dash:
            if self.Rect().colliderect(self.game.player.Rect()):
                self.game.player.impact = 10
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                # Generate many sparks and particles for a death explosion effect.
                for _ in range(30):
                    # --- ENEMY / PROJECTILE IMPACT PARTICLES ---
                    # Similar polar-to-Cartesian conversion is used here to spawn particles.
                    # Adding π to the angle flips their direction for a more chaotic explosion effect.
                    angle = random.random() * math.pi * 2  # Random angle in radians.
                    speed = random.random() * 5            # Random speed up to 5 units.
                    self.game.particles.append(
                        Particle(self.game, 'particle', self.Rect().center, velocity=[
                            math.cos(angle + math.pi) * speed * 0.5,  # Flip vector 180° for variety and slow it down.
                            math.sin(angle + math.pi) * speed * 0.5
                            ],
                            frame=random.randint(0, 7)
                        )
                    )

                # Add two stronger sparks in opposite directions for extra visual impact.
                self.game.sparks.append(Spark(self.Rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.Rect().center, math.pi, 5 + random.random()))
                # Return True to signal to the game loop that this enemy should be removed.
                return True

    def Render(self, surface, offset=(0, 0)):
        """
        Draw the enemy and its gun to the screen.
        :param surface: The target surface to draw on.
        :param offset: Camera offset for scrolling.
        """
        # Draw the enemy sprite using the base class render (handles animations).
        super().Render(surface, offset=offset)

        # Draw the enemy's gun based on its facing direction.
        if self.flip:
            # Facing left: flip the gun image horizontally and place it on the left side.
            surface.blit(
                pygame.transform.flip(self.game.assets['gun'], True, False),
                (
                    self.Rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0],
                    self.Rect().centery - offset[1]
                )
            )
        else:
            # Facing right: draw the gun normally on the right side.
            surface.blit(
                self.game.assets['gun'],
                (
                    self.Rect().centerx + 4 - offset[0],
                    self.Rect().centery - offset[1]
                )
            )



class Player(PhysicsEntity):
    """
    New class to extend PhysicsEntity to add player-exclusive behavior like 
    jumping, wall sliding, and setting the correct animation state based on movement.
    """
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)  # Initialize as a PhysicsEntity with the 'player' sprite.
        self.air_time = 0        # Counts how many frames the player has been in the air.
        self.jumps = 2           # Number of jumps remaining, used for multi-jumping/wall jumps
        self.wall_slide = False  # Whether the player is sliding down a wall.
        self.dashing = 0
        # Timer to freeze horizontal input after wall jump
        self.parry = 0
        self.velocity = [1, 0]
        self.impact = False
        


    def Update(self, tilemap, movement=(0, 0)):
        """
        Updates the player's physics, movement, and animation state for every frame.
        """
        super().Update(tilemap, movement=movement)  # Inherit PhysicsEntity's Update to handle basic movement & collisions.
        self.air_time += 1                          # Increment air time every frame.

        if self.air_time > 120:
            self.game.dead += 1
            self.game.screenshake = max(16, self.game.screenshake)
        
        # --Reset jump-related states when on the ground--
        if self.collisions['down']:  # If standing on top of a tile:
            self.air_time = 0        # Reset air time.
            self.jumps = 2         # Restore a jump, allowing the player to jump again

        self.wall_slide = False # set wall slide to false automaticlaly each frame in case the player has finished wall jumping
        # --Wall sliding logic--
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            # If touching a wall and has been of the ground for more than 4 frames:
            self.air_time = 5 
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)  # Limit downward velocity while sliding.

            # Flip sprite depending on wall side, default side is a;ways right
            if self.collisions['right']:
                self.flip = False  # Facing right wall, so look left.
            else:
                self.flip = True   # Facing left wall, so look right.
            
            self.Set_Action('wall_slide')  # Set animation to wall-slide.

        # --Set action based on movement state--
        if not self.wall_slide:  # If not sliding:
            if self.air_time > 4:       # If in the air for more than 4 frames, show jump animation.
                self.Set_Action('jump')
            elif movement[0] != 0:      # If moving horizontally, run.
                self.Set_Action('run')
            else:                        # Otherwise, idle animation.
                self.Set_Action('idle')

        # Gradually decrease the dash counter toward zero each frame.
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)   # If moving right, count down to 0.
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)   # If moving left, count up to 0.

        if self.parry > 0:
            self.parry = max(0, self.parry - 1)   # If moving right, count down to 0.
        if self.parry < 0:
            self.parry = min(0, self.parry + 1)   # If moving left, count up to 0.

        if self.impact > 0:
            self.impact = max(0, self.impact - 1)   # If moving right, count down to 0.

        if abs(self.parry) > 0:
            # \(A . B=A_{x}B_{x}).
            # projectile = [position[x,y], x_velocity, lifetime_counter]
            for projectile in self.game.projectiles.copy():
               distance = projectile[0][0] - self.pos[0] 
               direction = 1 if not self.flip else -1
               player_direction = pygame.Vector2(direction, 0)
               projectile_velocity= pygame.Vector2(projectile[1], 0)
               if player_direction.dot(projectile_velocity) < 0 and abs(distance) < 10:
                projectile[1] *= -1

                
    

        # If dashing for less than 10 frames (strong phase of dash), apply dash velocity and spawn dash particles.
        if abs(self.dashing) > 50:
            # Set horizontal velocity based on dash direction.
            self.velocity[0] = abs(self.dashing) / self.dashing * 8  # Sign gives direction, 8 is dash speed.
            
            # If dashing on the 10th frame (the transition from a strong -> weak phase of dash), slow down sharply.
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1

            # Create a trailing particle moving horizontally with the dash.
            # --DASH PARTICLE LOGIC--
            """
            When the player is dashing, spawn a particle streak behind them.
            The horizontal velocity is randomized but always follows the dash direction.
            abs(self.dashing / self.dashing) ensures positive magnitude, multiplied by ±1 for dash direction.
            Vertical velocity is zero so particles only streak horizontally.
            """
            player_velocity = [abs(self.dashing / self.dashing * random.random() * 3), 0] 
            self.game.particles.append(
                Particle(self.game, 'particle', self.Rect().center, velocity=player_velocity, frame=random.randint(0, 7))
            )

        # At the start or end of a dash (values 60 or 50), create a burst of particles.
        if abs(self.dashing) in {60, 50}:
            for i in range(20):      
                # Pick a random angle for the particle burst.
                angle = random.random() * math.pi * 2
                # Random speed between 0.5 and 1.0.
                speed = random.random() * 0.5 + 0.5
                # Convert polar coordinates to velocity vector.
                """
                    Polar coordinates define a point's location using:
                    - Its radial distance (r) from a fixed point called the pole (usually the origin).
                    - An angle (θ) measured from a fixed direction called the polar axis.
                    Coordinates are written as (r, θ).

                    To convert a vector from polar coordinates (magnitude r, angle θ) to Cartesian coordinates (x, y),
                    use the formulas: x = r * cos(θ) and y = r * sin(θ)

                    Why this works:
                    - The magnitude r is the hypotenuse of a right-angled triangle.
                    - The angle θ is measured from the positive x-axis.
                    - x is the adjacent side of the triangle (next to θ).
                    - y is the opposite side of the triangle (across from θ).

                    Using basic trigonometry:
                    - cos(θ) = adjacent / hypotenuse = x / r  ->  x = r * cos(θ)
                    - sin(θ) = opposite / hypotenuse = y / r  ->  y = r * sin(θ)
                """

                player_velocity = [speed * math.cos(angle), speed * math.sin(angle) ]
                # Spawn a particle at the player's center.
                self.game.particles.append(
                    Particle(self.game, 'particle', self.Rect().center, velocity=player_velocity, frame=random.randint(0, 7))
                )


        # --Apply horizontal friction to stop forced forwards velocity (deceleration)--
        if self.velocity[0] > 0:  # Moving right, reduce speed toward 0.
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:                     # Moving left, reduce speed toward 0.
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def Render(self, surface, offset=(0, 0)):
        """
        Overrides the default PhysicsEntity render:
        During the strongest part of a dash (>50), the player sprite is not rendered.
        This creates a 'blink' effect while particles simulate the dash trail.
        """
        if abs(self.dashing) <= 50:
            super().Render(surface, offset=offset)

    def Jump(self):
        """
        Handles jumping logic, including wall jumps and regular jumps.
        Returns True if a wall jump occurred, future use includes events.
        """
        # --Wall jump logic--
        if self.wall_slide:
            # Wall jump off a left wall: flip is True when facing right wall.

            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 4.5    # Push away from wall horizontally.
                self.velocity[1] = -2   # Jump upward.
                self.air_time = 5         # Reset air time to avoid immediate fall.
                self.jumps = max(0, self.jumps - 1)  # Use up a jump.
                return True

            # Wall jump off a right wall.
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -4.5   # Push away from wall horizontally.
                self.velocity[1] = -2   # Jump upward.
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True

        # --Normal jump logic--
        if self.jumps:            # If jumps are available:
            self.velocity[1] = -3 # Launch upward.
            self.jumps -= 1       # Decrease jump count.
            self.air_time = 5     # Mark as airborne for a short time.
            self.game.sfx['jump'].play()
            print(self.jumps)

    def Dash(self):
        """
        Starts a dash movement in the direction the player is facing.
        Uses 'dashing' as a counter: positive values for right dash, negative for left dash.
        """
        if not self.dashing:             # Only allow dash if not already dashing.
            self.game.sfx['dash'].play()
            if self.flip:               # flip=True means facing left.
                self.dashing = -60      # Negative value indicates left dash.
            else:                       
                self.dashing = 60       # Positive value indicates right dash.
    
    def Parry(self):
        if not self.parry:
            if self.flip:
                self.parry = -60
            else:
                self.parry = 60