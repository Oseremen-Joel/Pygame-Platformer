import random

"""
Parallax layering is a design technique that creates an illusion of depth on a 2D screen 
by making different layers of content move at different speeds during camera scrollimg
Closer layers move faster, while distant layers move slower, like real life
where nearby objects appear to whiz by but distant ones remain almost stationary.
"""

class Cloud:
    """
    Represents a single cloud in the background.
    Handles its position, speed, depth (parallax factor), and rendering.
    """
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos)     # Current position of the cloud (x, y) as a mutable list
        self.img = img           # Pygame surface representing the cloud image
        self.speed = speed       # Horizontal movement speed of the cloud
        self.depth = depth       # Parallax depth factor. 
        """
        The smaller the depth, the slower the cloud moves relative to the camera
        This makes the cloud appear further away (Vice versa for a higher depth)
        """

    def Update(self):
        """
        Moves the cloud horizontally based on its speed.
        """
        self.pos[0] += self.speed  # Move the cloud to the right each frame

    def Render(self, surface, offset=(0, 0)):
        """
        Draws the cloud on the screen, applying parallax scrolling based on depth.
        Uses modulo wrapping so clouds repeat continuously across the screen.
        """
        # Adjust position by the camera offset scaled by depth (parallax effect)
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)

        # Wrap the cloud around the screen edges to create an endless sky
        # The cloud only reappear after going completely off the screen  'surface.get_width() + self.img.get_width()'
        # The cloud reappears slightly outside the screen '-self.img.get_width()'
        surface.blit(
            self.img,
            (
                render_pos[0] % (surface.get_width() + self.img.get_width()) - self.img.get_width(),
                render_pos[1] % (surface.get_height() + self.img.get_height()) - self.img.get_height()
            )
        )

class Clouds:
    """
    Manages a collection of Cloud objects.
    Handles creation, updating positions, depth sorting, and rendering of multiple clouds.
    """
    def __init__(self, cloud_images, count=16):
        self.clouds = []

        # Create a specified number of clouds with random positions, images, speeds, and depths
        for i in range(count):
            self.clouds.append(
                Cloud(
                    (random.random() * 99999, random.random() * 99999),  # Random initial position far away
                    random.choice(cloud_images),                        # Random cloud image
                    random.random() * 0.05 + 0.05,                      # Random speed between 0.05 and 0.1
                    random.random() * 0.6 + 0.2                         # Random depth between 0.2 and 0.8
                )
            )

        # Sort clouds by depth so farther clouds render first (correct parallax layering)
        self.clouds.sort(key=lambda x: x.depth)

    def Update(self):
        """
        Updates all clouds by moving them based on their speed.
        """
        for cloud in self.clouds:
            cloud.Update()

    def Render(self, surface, offset=(0, 0)):
        """
        Renders all clouds on the screen, applying parallax effect.
        """
        for cloud in self.clouds:
            cloud.Render(surface, offset=offset)
