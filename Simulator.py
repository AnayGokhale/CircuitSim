import pygame
import sys
from Components import Wire, Battery, Resistor, LED
from Physics import path_matrix
# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
BREADBOARD_COLOR = (220, 200, 170)
HOLE_SIZE = 8
HOLE_COLOR = (40, 40, 40)
HOLE_SPACING = 20
BG_COLOR = (245, 245, 250)
PANEL_COLOR = (230, 230, 235)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
BUTTON_SELECTED = (50, 100, 150)
HOLE_HOVER_COLOR = (255, 200, 0)
HOLE_SELECTED_COLOR = (0, 200, 100)

class Hole:
    def __init__(self, x, y, row, col, is_rail=False):
        self.x = x
        self.y = y
        self.row = row
        self.col = col
        self.is_rail = is_rail
        self.radius = HOLE_SIZE // 2
        
    def draw(self, surface, color=HOLE_COLOR):
        pygame.draw.circle(surface, color, (self.x, self.y), self.radius)
        
    def contains(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx*dx + dy*dy <= (self.radius + 5)**2

class Button:
    def __init__(self, x, y, width, height, text, type):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.type = type
        self.selected = False
        
    def draw(self, surface, font):
        color = BUTTON_SELECTED if self.selected else BUTTON_COLOR
        if not self.selected and self.rect.collidepoint(pygame.mouse.get_pos()):
            color = BUTTON_HOVER
            
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class Dropdown:
    def __init__(self, x, y, width, height, options, default):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_option = default
        self.expanded = False
        self.option_rects = [pygame.Rect(x, y + (i+1)*height, width, height) for i in range(len(options))]

    def draw(self, surface, font):
        pygame.draw.rect(surface, (200, 200, 200), self.rect)
        text_surf = font.render(str(self.selected_option), True, (0, 0, 0))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

        if self.expanded:
            for i, opt in enumerate(self.options):
                pygame.draw.rect(surface, (220, 220, 220), self.option_rects[i])
                opt_surf = font.render(str(opt), True, (0, 0, 0))
                surface.blit(opt_surf, opt_surf.get_rect(center=self.option_rects[i].center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return None
            if self.expanded:
                for i, opt_rect in enumerate(self.option_rects):
                    if opt_rect.collidepoint(event.pos):
                        self.selected_option = self.options[i]
                        self.expanded = False
                        return self.selected_option
        return None

class BreadboardSimulator:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Breadboard Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        
        # Breadboard setup
        self.board_x = 50
        self.board_y = 150
        self.board_width = 850
        self.board_height = 450
        
        # Component selection
        self.active_component_txt = "Wire"
        self.active_component = Wire(0,0)
        self.first_hole = None
        self.hovered_hole = None
        self.components = []
        self.dropdown = None

        # Create UI
        self.create_buttons()
        self.create_holes()
        
        # Measurements
        self.measurements = {
            "Current": 0.0,
            "Voltage": 0.0,
            "Resistance": 0.0,
            "Power": 0.0
        }
    
    def create_buttons(self):
        self.buttons = []
        components = [Wire, Battery, Resistor, LED]
        component_text = ["Wire", "Battery", "Resistor", "LED"]
        for i, comp in enumerate(component_text):
            btn = Button(50 + i * 130, 30, 120, 45, comp, components[i])
            if comp == self.active_component_txt:
                btn.selected = True
            self.buttons.append(btn)
        self.run_button = Button(570, 30, 120, 45, "Run", None)
    
    def create_holes(self):
        self.holes = []
        
        # Top power rails (2 rows)
        for row in range(2):
            for col in range(40):
                x = self.board_x + 40 + col * HOLE_SPACING
                y = self.board_y + 30 + row * HOLE_SPACING
                self.holes.append(Hole(x, y, row, col, is_rail=True))
        
        # Main board: 5 rows, gap, 5 rows
        for section in range(2):
            y_offset = 100 if section == 0 else 240
            for row in range(5):
                for col in range(40):
                    x = self.board_x + 40 + col * HOLE_SPACING
                    y = self.board_y + y_offset + row * HOLE_SPACING
                    actual_row = row + 2 + (section * 6)  # Offset by rail rows
                    self.holes.append(Hole(x, y, actual_row, col, is_rail=False))
        
        # Bottom power rails (2 rows)
        for row in range(2):
            for col in range(40):
                x = self.board_x + 40 + col * HOLE_SPACING
                y = self.board_y + 380 + row * HOLE_SPACING
                actual_row = 13 + row
                self.holes.append(Hole(x, y, actual_row, col, is_rail=True))
    
    def draw_breadboard(self):
        # Main board
        pygame.draw.rect(self.screen, BREADBOARD_COLOR,
                        (self.board_x, self.board_y, self.board_width, self.board_height),
                        border_radius=10)
        
        # Draw holes
        for hole in self.holes:
            color = HOLE_COLOR
            if hole == self.hovered_hole:
                color = HOLE_HOVER_COLOR
            elif hole == self.first_hole:
                color = HOLE_SELECTED_COLOR
            hole.draw(self.screen, color)
        
        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.screen, self.font)
        self.run_button.draw(self.screen, self.font)

    def handle_click(self, pos):
        # Check buttons
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                for b in self.buttons:
                    b.selected = False
                btn.selected = True
                self.active_component_txt = btn.text
                if btn.type == Wire:
                    self.active_component = Wire(0,0)
                    self.dropdown = None
                elif btn.type == Battery:
                    self.dropdown = Dropdown(750, 30, 100, 30, [1.5, 3, 5, 9], 3)
                elif btn.type == Resistor:
                    self.dropdown = Dropdown(750, 30, 100, 30, [100, 220, 330, 1000], 220)
                elif btn.type == LED:
                    self.dropdown = Dropdown(750, 30, 100, 30, ["red", "green", "blue"], "red")
                return

        if self.run_button.rect.collidepoint(pos):
            print("Running simulation...")
            # TODO: Call physics simulation
            components = self.components
            path = path_matrix(components)
            print("Path matrix:", path)
            return
        
        # Check holes
        for hole in self.holes:
            if hole.contains(pos):
                if self.first_hole is None:
                    self.first_hole = hole
                    print(f"Start: row={hole.row}, col={hole.col}, rail={hole.is_rail}")
                else:
                    self.active_component.node1 = (self.first_hole.row, self.first_hole.col)
                    self.active_component.node2 = (hole.row, hole.col)
                    self.components.append(self.active_component)
                    print(f"End: row={hole.row}, col={hole.col}, rail={hole.is_rail}")
                    print(f"Placing {self.active_component.name}")
                    print(f"Current components: {[c.name for c in self.components]}")
                    # TODO: Create component
                    self.first_hole = None
                return
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.hovered_hole = None
                    for hole in self.holes:
                        if hole.contains(event.pos):
                            self.hovered_hole = hole
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.dropdown:
                        value = self.dropdown.handle_event(event)
                        if value is not None:
                            if self.active_component_txt == "Battery":
                                self.active_component = Battery(0, 0, value)
                            elif self.active_component_txt == "Resistor":
                                self.active_component = Resistor(0, 0, value)
                            elif self.active_component_txt == "LED":
                                self.active_component = LED(0, 0, 220, value)
                    self.handle_click(event.pos)
            
            self.screen.fill(BG_COLOR)
            
            # Draw UI            
            self.draw_breadboard()
            if self.dropdown:
                self.dropdown.draw(self.screen, self.font)

            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = BreadboardSimulator()
    app.run()