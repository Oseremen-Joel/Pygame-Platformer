# --Particle.py--
class Particle:
    """
    Represents a single particle in the game world (e.g., a falling leaf).
    Handles its animation, position updates, and rendering.
    """
    def __init__(self, game, particle_type, pos, velocity=[0,0], frame=0):
        self.game = game
        self.type = particle_type
        self.pos = list(pos) # Current particle position
        self.velocity = list(velocity) # Movement velocity per frame
        # Create an animation copy for this particle so multiple particles can use the same asset independently.
        self.animation = self.game.assets['particle/' + particle_type].Copy()
        self.animation.frame = frame # Start at a random frame for variety
  
    def Update(self):
        """
        Updates the particle's position and animation state.
        Returns True if the particle's animation is done and it should be removed.
        """
        kill = False
        if self.animation.done: # If the animation has finished, mark for removal.
            kill = True

        # Apply velocity to move the particle.
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        # Advance the animation by one frame.
        self.animation.Update()

        return kill

    def Render(self, surface, offset=(0, 0)):
        """
        Draws the particle centered on its position, accounting for camera offset.
        """
        image = self.animation.Image()
        surface.blit(
            image,
            (
                self.pos[0] - offset[0] - image.get_width() // 2,
                self.pos[1] - offset[1] - image.get_height() // 2
            )
        )
