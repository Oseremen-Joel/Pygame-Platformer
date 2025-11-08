import os
import pygame

BASE_IMG_PATH = 'data/images/'  # Base folder where all images are stored

def load_image(path):
    """
    Loads a single image from disk, converts it for fast blitting,
    and sets black (0,0,0) as transparent.
    """
    image = pygame.image.load(BASE_IMG_PATH + path).convert()  # Load and convert for performance
    image.set_colorkey((0, 0, 0))  # Make black pixels transparent
    return image

def load_images(path):
    """
    Loads all images in a folder into a list.
    The files are sorted alphabetically so animation frames are in order.
    Returns a list of Pygame surfaces.
    """
    images = []
    for image_name in sorted(os.listdir(BASE_IMG_PATH + path)):  # Loop through all files in folder
        images.append(load_image(path + '/' + image_name))        # Load each image and append
    return images                                                 # Return full list of images

class Animation:
    """
    Represents a looping or one-time animation using a list of images.
    Handles frame timing, looping, and provides the current image.
    """
    def __init__(self, images, image_duration=5, loop=True):
        self.images = images                # List of Pygame surfaces for animation frames
        self.loop = loop                    # Whether the animation loops
        self.image_duration = image_duration # Frames to display each image before advancing
        self.done = False                   # Flag for when a non-looping animation has finished
        self.frame = 0                      # Current frame counter

    def Copy(self):
        """
        Creates a new Animation with the same images and settings.
        Note: shares the same image list to save memory.
        """
        return Animation(self.images, self.image_duration, self.loop)
    
    def Update(self):
        """
        Advances the animation frame counter.
        - For looping animations: wraps around after the last frame.
        - For non-looping animations: stops at the last frame and sets done=True.
        """
        if self.loop:
            # Wrap around using modulo for infinite looping
            self.frame = (self.frame + 1) % (self.image_duration * len(self.images))
        else:
            # Increase frame but clamp to the last frame index
            self.frame = min(self.frame + 1, self.image_duration * len(self.images) - 1)
            # If we’ve reached the end, mark animation as done
            if self.frame >= self.image_duration * len(self.images) - 1:
                self.done = True
    
    def Image(self):
        """
        Returns the current frame’s image to be drawn.
        Uses integer division to pick the correct frame based on image_duration.
        """
        return self.images[int(self.frame / self.image_duration)]
