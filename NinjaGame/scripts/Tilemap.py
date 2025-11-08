import pygame
import json

# AUTOTILE_MAP: Maps a set of neighboring directions to a specific tile variant index.
# Each key is a tuple of directions (dx, dy) representing connected neighbors.
# This allows automatic selection of edge/corner tiles based on surrounding tiles.
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,                       # neighbors: right + down
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,              # right + down + left
    tuple(sorted([(-1, 0), (0, 1)])): 2,                      # left + down
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,             # left + up + down
    tuple(sorted([(-1, 0), (0, -1)])): 4,                     # left + up
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,             # left + up + right
    tuple(sorted([(1, 0), (0, -1)])): 6,                      # right + up
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,              # right + up + down
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,     # all four directions
}

# Offsets for all 8 surrounding tiles plus the center tile.
# Used to check which tiles exist near a position.
NEIGHBOR_OFFSET = [(-1, 0), (-1, -1), (0, -1), (1, -1),
                   (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]

# Sets of tile types considered "solid" for collisions and autotiling.
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.tile_size = tile_size       # Width/height of a single tile in pixels
        self.game = game                 # Reference to the main game (for assets)
        self.tilemap = {}                # Dictionary of grid-aligned tiles: {"x;y": {pos,type,variant}}
        self.offgrid_tiles = []          # Tiles not snapped to the grid (decorations)

       
    def Extract(self, id_pairs, keep=False):
        """
        Extracts tiles from both on-grid (self.tilemap) and off-grid (self.offgrid_tiles) collections
        that match specific (type, variant) pairs.
        
        Arguments:
        - id_pairs: A list of (tile_type, variant) tuples to match against tiles.
        - keep: If False, removes matched tiles from the tilemap/offgrid list after copying them.
                If True, keeps the original tiles intact.

        Returns:
        - A list of matching tile dictionaries, with their positions converted to pixel coordinates.
        """
        matches = []
        # --- Search off-grid tiles ---
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())        # Store a copy of the matched tile
                if not keep:
                    self.offgrid_tiles.remove(tile)  # Remove it from the list if not keeping

        # --- Search on-grid tiles ---
        for location in self.tilemap:
            tile = self.tilemap[location]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())         # Store a copy of the matched tile
                # Convert tile position from grid coordinates to pixel coordinates
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[location]      # Remove the tile from the map if not keeping
        return matches


    def Tiles_Around(self, pos):
        """
        Return all tiles around a world position `pos` (in pixels).
        Converts pos -> tile coordinates and checks all offsets in NEIGHBOR_OFFSET.
        """
        tiles = []
        tile_location = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSET:
            check_location = str(tile_location[0] + offset[0]) + ';' + str(tile_location[1] + offset[1])
            if check_location in self.tilemap:
                tiles.append(self.tilemap[check_location])
        return tiles
    
    def Physics_Rects_Around(self, pos):
        """
        Return pygame.Rect objects for all solid tiles around a position.
        These rects are used for collision detection.
        """
        rects = []
        for tile in self.Tiles_Around(pos):
            if tile['type'] in PHYSICS_TILES:  # Only consider solid tiles
                rects.append(
                    pygame.Rect(
                        tile['pos'][0] * self.tile_size,
                        tile['pos'][1] * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
        return rects
    
    def Render(self, surface, offset=(0, 0)):
        """
        Draw all tiles on the given surface, shifted by the camera offset.
        First draw off-grid decorations, then draw grid-aligned tiles
        only within the visible screen area.
        """
        # Draw non-grid tiles directly (e.g., decorations)
        for tile in self.offgrid_tiles:
            surface.blit(
                self.game.assets[tile['type']][tile['variant']],
                (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1])
            )

       
        """
        Draws the visible portion of the grid-aligned tiles which improves performance for large maps.

        - offset[0] // tile_size -> converts the first tile (top left of the screen) from pos to tile coordinates in the x axis
        - (offset[0] + surface.get_width()) // tile_size + 1 -> converts the last tile (bottom right of the screen) from pos to tile coordinates in the x axis, + 1 as range() ends at 1 less than the stop value
        - Same applies for the y-axis
        - For each visible tile, we:
            • Look up its image using tile['type'] and tile['variant'].
            • Multiply tile['pos'] by tile_size to convert grid coords -> world coords.
            • Subtract offset to place it correctly relative to the camera.
        """
        for x in range(offset[0] // self.tile_size, (offset[0] + surface.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surface.get_height()) // self.tile_size + 1):
                location = str(x) + ';' + str(y)
                if location in self.tilemap:
                    tile = self.tilemap[location]
                    surface.blit(
                        self.game.assets[tile['type']][tile['variant']],
                        (tile['pos'][0] * self.tile_size - offset[0],
                         tile['pos'][1] * self.tile_size - offset[1])
                    )

    def Save(self, path):
        """
        Save the current tilemap state to a JSON file.
        Includes the tilemap dictionary, tile size, and off-grid tiles.
        """
        with open(path, 'w') as f:
            json.dump(
                {'tilemap': self.tilemap,
                 'tile_size': self.tile_size,
                 'offgrid': self.offgrid_tiles},
                f, indent=4
            )
    
    def Solid_Check(self ,pos):
        tile_location = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_location in self.tilemap:
            if self.tilemap[tile_location]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_location]
    
    def Load(self, path):
        """
        Load tilemap data from a JSON file and restore state.
        """
        with open(path, 'r') as f:
            map_data = json.load(f)

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def AutoTile(self):
        """
        Automatically chooses which tile variant to display based on its neighbors.
        
        Logic for autotiling:
        - For every tile in self.tilemap:
            • Check the four important directions: right (1,0), left (-1,0), up (0,-1), down (0,1).
            • For each neighbor in these directions:
                – Build a string key like "x;y" for the neighbor’s grid location.
                – If that location exists and is the same type as the current tile,
                  add the direction vector to a set called neighbors.
            • Sort and convert neighbors to a tuple so it can be matched reliably
              (order doesn’t matter, sorting makes the tuple hashable and comparable).
            • Look up this tuple in AUTOTILE_MAP to find the correct variant index.
            • Update tile['variant'] so edges, corners, and center tiles match visually.
        - This creates smooth transitions between tiles: corners, edges, T-junctions, etc.
        """
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            # Check each of the four directions for same-type neighbors
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap and self.tilemap[check_loc]['type'] == tile['type']:
                    neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            # If the tile type supports autotiling and neighbors match a pattern, update its variant
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]
