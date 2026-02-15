import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BG_COLOR = (245, 245, 250)

# Resistor Colors
RESISTOR_COLORS = {
    "black": (0, 0, 0),
    "brown": (139, 69, 19),
    "red": (255, 0, 0),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "violet": (238, 130, 238),
    "gray": (128, 128, 128),
    "white": (255, 255, 255),
    "gold": (212, 175, 55),
    "silver": (192, 192, 192)
}

COLOR_ORDER = list(RESISTOR_COLORS.keys())

class ResistorVisual:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.bands = ["brown", "black", "red", "gold"] # 1k ohm, 5% tolerance default
        self.band_rects = []
        self.update_band_rects()

    def update_band_rects(self):
        self.band_rects = []
        # Define band positions relative to width
        # Body is beige/tan
        # Bands are strips
        
        # 4 bands:
        # 1st digit: ~20%
        # 2nd digit: ~35%
        # Multiplier: ~50%
        # Tolerance: ~80%
        
        band_w = self.rect.width * 0.08
        
        positions = [0.2, 0.35, 0.5, 0.8]
        
        for pos in positions:
            bx = self.rect.x + (self.rect.width * pos)
            by = self.rect.y
            self.band_rects.append(pygame.Rect(bx, by, band_w, self.rect.height))

    def draw(self, surface):
        lead_color = (150, 150, 150)
        lead_thickness = int(self.rect.height * 0.15)
        mid_y = self.rect.centery
        
        pygame.draw.line(surface, lead_color, (self.rect.x - 50, mid_y), (self.rect.x + 10, mid_y), lead_thickness)
        pygame.draw.line(surface, lead_color, (self.rect.right - 10, mid_y), (self.rect.right + 50, mid_y), lead_thickness)
        
        body_color = (222, 184, 135)
        shading_color = (180, 140, 100)
        highlight_color = (240, 220, 180)
        
        width = self.rect.width
        height = self.rect.height
        
        end_w = width * 0.15
        center_w = width - (2 * end_w)
        
        left_cap_rect = pygame.Rect(self.rect.x, self.rect.y, end_w * 1.5, height)
        pygame.draw.ellipse(surface, body_color, left_cap_rect)
        
        right_cap_rect = pygame.Rect(self.rect.right - end_w * 1.5, self.rect.y, end_w * 1.5, height)
        pygame.draw.ellipse(surface, body_color, right_cap_rect)
        
        center_rect = pygame.Rect(self.rect.x + end_w, self.rect.y + height*0.1, center_w, height*0.8)
        pygame.draw.rect(surface, body_color, center_rect)

        band_w = width * 0.08
        
        for i, band_name in enumerate(self.bands):
            color = RESISTOR_COLORS.get(band_name, (0,0,0))
            rect = self.band_rects[i]            
            pygame.draw.rect(surface, color, rect)
            highlight_rect = pygame.Rect(rect.x, rect.y + height*0.2, rect.width, height*0.1)
            pygame.draw.rect(surface, (255, 255, 255, 50), highlight_rect)
            
        shine_rect = pygame.Rect(self.rect.x, self.rect.y + height*0.15, width, height*0.1)
        s = pygame.Surface((width, int(height*0.1)), pygame.SRCALPHA)
        s.fill((255, 255, 255, 80))
        surface.blit(s, (self.rect.x, self.rect.y + height*0.15))
        
        shade_rect = pygame.Rect(self.rect.x, self.rect.bottom - height*0.2, width, height*0.15)
        s2 = pygame.Surface((width, int(height*0.15)), pygame.SRCALPHA)
        s2.fill((0, 0, 0, 50))
        surface.blit(s2, (self.rect.x, self.rect.bottom - height*0.2))
        
    def handle_click(self, pos):
        for i, rect in enumerate(self.band_rects):
            if rect.collidepoint(pos):
                current_idx = COLOR_ORDER.index(self.bands[i])
                next_idx = (current_idx + 1) % len(COLOR_ORDER)
                self.bands[i] = COLOR_ORDER[next_idx]
                return True
        return False

def main():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Resistor Visual Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    resistor = ResistorVisual(200, 250, 400, 100)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                resistor.handle_click(event.pos)

        screen.fill(BG_COLOR)
        
        resistor.draw(screen)
        
        text = font.render("Click bands to change colors", True, (0,0,0))
        screen.blit(text, (250, 150))
        
        stats = f"Bands: {', '.join(resistor.bands)}"
        stats_surf = pygame.font.Font(None, 24).render(stats, True, (50, 50, 50))
        screen.blit(stats_surf, (200, 400))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
