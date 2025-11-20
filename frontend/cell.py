import pygame
import consts

class Cell:
    def __init__(self, surface, sx, sy, color=None):
        self.sx = sx
        self.sy = sy
        self.size = consts.cell_size
        self.surface = surface
        self.color = color if color else consts.back_color
        
        # Draw cell border (grid lines)
        pygame.draw.rect(
            surface, 
            (50, 50, 60),  # Grid line color
            (sx, sy, consts.cell_size, consts.cell_size), 
            1
        )
        
        # Fill cell with initial color
        self.set_color(self.color)
    
    def set_color(self, color):
        """Update cell color"""
        self.color = color
        
        # Draw filled rectangle (leaving 2px border for grid)
        pygame.draw.rect(
            self.surface, 
            color, 
            (self.sx + 1, self.sy + 1, self.size - 2, self.size - 2)
        )
        
        # Update only this cell's area for better performance
        pygame.display.update(pygame.Rect(self.sx, self.sy, self.size, self.size))