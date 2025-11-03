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

class NumericCounter:
    def __init__(self, x, y, width, height, label, value=0, step=1, min_val=0, max_val=1000):
        self.rect = pygame.Rect(x, y, width, height)
        self.value = value
        self.step = step
        self.min_val = min_val
        self.max_val = max_val
        self.label = label
        self.minus_rect = pygame.Rect(x - 30, y, 25, height)
        self.plus_rect = pygame.Rect(x + width + 5, y, 25, height)

    def draw(self, surface, font):
        label_surf = font.render(self.label, True, (0,0,0))
        surface.blit(label_surf, (self.rect.x - 80, self.rect.y + 5))

        pygame.draw.rect(surface, (230,230,230), self.rect)
        val_surf = font.render(str(self.value), True, (0,0,0))
        surface.blit(val_surf, val_surf.get_rect(center=self.rect.center))

        pygame.draw.rect(surface, (200,200,200), self.minus_rect)
        pygame.draw.rect(surface, (200,200,200), self.plus_rect)
        surface.blit(font.render("-", True, (0,0,0)), self.minus_rect.move(7,2))
        surface.blit(font.render("+", True, (0,0,0)), self.plus_rect.move(7,2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.minus_rect.collidepoint(event.pos):
                self.value = max(self.min_val, self.value - self.step)
                return self.value
            elif self.plus_rect.collidepoint(event.pos):
                self.value = min(self.max_val, self.value + self.step)
                return self.value
        return None


class Dropdown:
    def __init__(self, x, y, width, height, label, options, default):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_option = default
        self.expanded = False
        self.label = label

    def draw(self, surface, font):
        label_surf = font.render(self.label, True, (0,0,0))
        surface.blit(label_surf, (self.rect.x - 80, self.rect.y + 5))

        pygame.draw.rect(surface, (230,230,230), self.rect)
        text_surf = font.render(str(self.selected_option), True, (0,0,0))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

        if self.expanded:
            for i, opt in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y + (i+1)*self.rect.height,
                                       self.rect.width, self.rect.height)
                pygame.draw.rect(surface, (200,200,200), opt_rect)
                opt_surf = font.render(str(opt), True, (0,0,0))
                surface.blit(opt_surf, opt_surf.get_rect(center=opt_rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return None
            if self.expanded:
                for i, opt in enumerate(self.options):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.y + (i+1)*self.rect.height,
                                           self.rect.width, self.rect.height)
                    if opt_rect.collidepoint(event.pos):
                        self.selected_option = self.options[i]
                        self.expanded = False
                        return self.selected_option
                self.expanded = False
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
        self.param_widget = None

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
                    # No widget needed
                    self.active_component = Wire(0,0)
                    self.param_widget = None
                elif btn.type == Battery:
                    # Voltage widget
                    self.param_widget = NumericCounter(750, 30, 60, 30, "Voltage", value=3, step=1, min_val=1, max_val=12)
                elif btn.type == Resistor:
                    # Resistance widget
                    self.param_widget = NumericCounter(750, 30, 60, 30, "Resistance", value=220, step=10, min_val=10, max_val=10000)
                elif btn.type == LED:
                    # Color widget
                    self.param_widget = Dropdown(750, 30, 100, 30, "Color", ["red","green","blue"], "red")
                return

        if self.run_button.rect.collidepoint(pos):
            print("Running simulation...")
            # TODO: Call physics simulation
            components = self.components
            # incidence matrix BROKEN
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
        # Main loop
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
                    if self.param_widget:
                        value = self.param_widget.handle_event(event)
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
            if self.param_widget:
                self.param_widget.draw(self.screen, self.font)

            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = BreadboardSimulator()
    app.run()