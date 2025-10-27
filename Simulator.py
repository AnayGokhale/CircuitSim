'''
import tkinter as tk

BREADBOARD_WIDTH = 500
BREADBOARD_HEIGHT = 300
BREADBOARD_COLOR = "#C0C0C0"
HOLE_SIZE = 6
HOLE_COLOR = "#000000"
HOLE_SPACING = 15
CENTER_CHANNEL_HEIGHT = 3 * HOLE_SPACING
RAIL_COUNT = 2

class BreadboardSimulatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Python Breadboard Simulator")

        self.active_component_type = "Wire"
        self.placement_node_1 = None
        self.node_locations = []
        self.components = []
        self.hover_rect = None
        
        self.canvas = tk.Canvas(
            master, 
            width=BREADBOARD_WIDTH + 200, 
            height=BREADBOARD_HEIGHT + 200, 
            bg="#FFFFFF"
        )
        self.canvas.pack(padx=20, pady=20)
        
        self.draw_breadboard_base(50, 150)
        
        self.draw_info_panel()

    def draw_breadboard_base(self, start_x, start_y):
        # Draw the main plastic block
        self.canvas.create_rectangle(
            start_x, start_y, 
            start_x + BREADBOARD_WIDTH, start_y + BREADBOARD_HEIGHT,
            fill=BREADBOARD_COLOR, 
            outline=HOLE_COLOR
        )
        
    def draw_info_panel(self):
        self.canvas.create_text(
            BREADBOARD_WIDTH + 60, 50, 
            text="Measurements & Controls", 
            font=("Arial", 10, "bold")
        )
        self.measurement_label = self.canvas.create_text(
            BREADBOARD_WIDTH + 60, 80, 
            text="Current: 0.0A\nVoltage: 0.0V", 
            anchor="nw",
            font=("Courier", 10)
        )


if __name__ == "__main__":
    root = tk.Tk()
    
    # Instantiate the application
    app = BreadboardSimulatorApp(root)
    
    # Start the Tkinter event loop
    root.mainloop()
'''
import pygame
import sys

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
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.selected = False
        
    def draw(self, surface, font):
        color = BUTTON_SELECTED if self.selected else BUTTON_COLOR
        if not self.selected and self.rect.collidepoint(pygame.mouse.get_pos()):
            color = BUTTON_HOVER
            
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

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
        self.active_component = "Wire"
        self.first_hole = None
        self.hovered_hole = None
        
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
        components = ["Wire", "Battery", "Resistor", "LED"]
        for i, comp in enumerate(components):
            btn = Button(50 + i * 130, 30, 120, 45, comp)
            if comp == self.active_component:
                btn.selected = True
            self.buttons.append(btn)
        self.run_button = Button(570, 30, 120, 45, "Run")
        
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
    
    def draw_panel(self):
        panel_x = 950
        panel_y = 150
        
        pygame.draw.rect(self.screen, PANEL_COLOR,
                        (panel_x, panel_y, 220, 350), border_radius=10)
        
        # Title
        title = self.font.render("Measurements", True, (0, 0, 0))
        self.screen.blit(title, (panel_x + 40, panel_y + 20))
        
        # Values
        y = panel_y + 70
        for label, value in self.measurements.items():
            unit = {"Current": "A", "Voltage": "V", "Resistance": "Ω", "Power": "W"}[label]
            text = f"{label}: {value:.3f} {unit}"
            surf = self.small_font.render(text, True, (0, 0, 0))
            self.screen.blit(surf, (panel_x + 20, y))
            y += 50
    
    def handle_click(self, pos):
        # Check buttons
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                for b in self.buttons:
                    b.selected = False
                btn.selected = True
                self.active_component = btn.text
                return
        
        if self.run_button.rect.collidepoint(pos):
            print("Running simulation...")
            # TODO: Call physics simulation
            return
        
        # Check holes
        for hole in self.holes:
            if hole.contains(pos):
                if self.first_hole is None:
                    self.first_hole = hole
                    print(f"Start: row={hole.row}, col={hole.col}, rail={hole.is_rail}")
                else:
                    print(f"End: row={hole.row}, col={hole.col}, rail={hole.is_rail}")
                    print(f"Placing {self.active_component}")
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
            
            self.screen.fill(BG_COLOR)
            
            # Draw UI
            for btn in self.buttons:
                btn.draw(self.screen, self.font)
            self.run_button.draw(self.screen, self.font)
            
            self.draw_breadboard()
            self.draw_panel()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = BreadboardSimulator()
    app.run()