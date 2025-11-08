import math
import pygame

class Spark:
    def __init__(self, pos, angle, speed):
        self.pos = list(pos)  # Spark's current position.
        self.angle = angle    # Movement direction in radians.
        self.speed = speed    # Speed (magnitude of velocity).

    def Update(self):
        # Move sparks by converting their polar velocity (angle and speed) to Cartesian components.
        self.pos[0] += math.cos(self.angle) * self.speed  # Horizontal movement based on angle and speed.
        self.pos[1] += math.sin(self.angle) * self.speed  # Vertical movement based on angle and speed.
        # Gradually reduce speed to simulate friction or air resistance.
        self.speed = max(0, self.speed - 0.1)
        # If speed has dropped to zero, return True to signal removal.
        return not self.speed

    def Render(self, surface, offset=(0, 0)):
        # Construct a diamond-shaped polygon pointing along the spark's movement.
        render_points = [
            # Tip pointing forward (scaled ×3 for a long tail).
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0],
            self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            # Right side: perpendicular vector (angle + π/2).
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0],
            self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            # Back tip: reversed vector (angle + π).
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0],
            self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            # Left side: perpendicular vector (angle - π/2).
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0],
            self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1]),
        ]
        # The resulting polygon resembles a stretched diamond that shrinks as speed decreases.
        pygame.draw.polygon(surface, (255, 255, 255), render_points)
      




