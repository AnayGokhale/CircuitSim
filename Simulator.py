import pygame
import sys
import math
from Components import Wire, Battery, Resistor, LED
from Physics import generate_incidence_matrix, ModifiedNodalAnalysis
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


class UnionFind:
    def __init__(self, items):
        self.parent = {item: item for item in items}
        self.node_ids = {item: None for item in items}

    def find(self, item):
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item1, item2):
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 != root2:
            self.parent[root2] = root1
            return True
        return False

    def set_id(self, item, node_id):
        root = self.find(item)
        self.node_ids[root] = node_id

    def get_id(self, item):
        root = self.find(item)
        return self.node_ids.get(root)

class Hole:
# Represents a hole on the breadboard
    def __init__(self, x, y, row, col, is_rail=False, node_id=None):
        self.x = x
        self.y = y
        self.row = row
        self.col = col
        self.is_rail = is_rail
        self.radius = HOLE_SIZE // 2
        self.node_id = node_id
        
    def draw(self, surface, color=HOLE_COLOR):
        pygame.draw.circle(surface, color, (self.x, self.y), self.radius)
        
    def contains(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx*dx + dy*dy <= (self.radius + 5)**2

class Button:
# UI Button for component selection 
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
        
        # Text input state
        self.text = str(value)
        self.active = False
        
        # Determine button layout relative to main value rect
        btn_w = 30
        self.minus_rect = pygame.Rect(x - btn_w - 5, y, btn_w, height)
        self.plus_rect = pygame.Rect(x + width + 5, y, btn_w, height)

    def set_position(self, x, y):
        # Update positions if moved
        btn_w = 30
        self.rect.topleft = (x, y)
        self.minus_rect.topleft = (x - btn_w - 5, y)
        self.plus_rect.topleft = (x + self.rect.width + 5, y)

    def bounds(self):
        # Return a rect that covers label + minus + value + plus, for outside-click detection
        left = self.minus_rect.x
        top = self.rect.y
        right = self.plus_rect.right
        bottom = self.rect.bottom
        return pygame.Rect(left - 100, top, (right - left) + 100, bottom - top)

    def draw(self, surface, font):
        label_surf = font.render(self.label, True, (0,0,0))
        label_y = self.rect.centery - label_surf.get_height() // 2
        surface.blit(label_surf, (self.rect.x - 90 - label_surf.get_width()//2, label_y))

        bg_color = (255, 255, 255) if self.active else (230, 230, 230)
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=4)
        if self.active:
            pygame.draw.rect(surface, (0, 100, 255), self.rect, 2, border_radius=4)

        display_text = self.text if self.active else str(self.value)
        val_surf = font.render(display_text, True, (0,0,0))
        surface.blit(val_surf, val_surf.get_rect(center=self.rect.center))

        # Buttons
        pygame.draw.rect(surface, (200,200,200), self.minus_rect, border_radius=4)
        pygame.draw.rect(surface, (200,200,200), self.plus_rect, border_radius=4)
        surface.blit(font.render("-", True, (0,0,0)), font.render("-", True, (0,0,0)).get_rect(center=self.minus_rect.center))
        surface.blit(font.render("+", True, (0,0,0)), font.render("+", True, (0,0,0)).get_rect(center=self.plus_rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.minus_rect.collidepoint(event.pos):
                self.value = max(self.min_val, self.value - self.step)
                self.text = str(self.value)
                return self.value
            elif self.plus_rect.collidepoint(event.pos):
                self.value = min(self.max_val, self.value + self.step)
                self.text = str(self.value)
                return self.value
            elif self.rect.collidepoint(event.pos):
                self.active = True
                self.text = str(self.value)
            else:
                if self.active:
                    try:
                        val = int(self.text)
                        self.value = min(self.max_val, max(self.min_val, val))
                    except ValueError:
                        pass
                    self.text = str(self.value)
                    self.active = False
                    return self.value
                self.active = False
                self.text = str(self.value)

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                try:
                    val = int(self.text)
                    self.value = min(self.max_val, max(self.min_val, val))
                except ValueError:
                    pass
                self.text = str(self.value)
                self.active = False
                return self.value
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if event.unicode.isdigit():
                    self.text += event.unicode
        return None

class Dropdown:

    def __init__(self, x, y, width, height, label, options, default):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_option = default
        self.expanded = False
        self.label = label

    def set_position(self, x, y):
        self.rect.topleft = (x, y)

    def option_rect(self, i):
        # Each option extends directly below the main box
        return pygame.Rect(self.rect.x, self.rect.y + (i+1)*self.rect.height, self.rect.width, self.rect.height)

    def bounds(self):
        # Full area including expanded options
        height = self.rect.height * (1 + (len(self.options) if self.expanded else 0))
        return pygame.Rect(self.rect.x, self.rect.y, self.rect.width, height)

    def draw(self, surface, font):
        # Label
        label_surf = font.render(self.label, True, (0,0,0))
        surface.blit(label_surf, (self.rect.x - 80, self.rect.y + 5))

        # Main box
        pygame.draw.rect(surface, (230,230,230), self.rect, border_radius=4)
        text_surf = font.render(str(self.selected_option), True, (0,0,0))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

        # Expanded options below the button-aligned box
        if self.expanded:
            for i, opt in enumerate(self.options):
                opt_rect = self.option_rect(i)
                pygame.draw.rect(surface, (200,200,200), opt_rect)
                opt_surf = font.render(str(opt), True, (0,0,0))
                surface.blit(opt_surf, opt_surf.get_rect(center=opt_rect.center))

    def handle_event(self, event):
        # Toggle expansion or select option
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return None
            if self.expanded:
                for i, _ in enumerate(self.options):
                    if self.option_rect(i).collidepoint(event.pos):
                        self.selected_option = self.options[i]
                        self.expanded = False
                        return self.selected_option
                # Click away closes it
                self.expanded = False
        return None

class BreadboardSimulator:
# Main application class
    def __init__(self):
        # Pygame setup
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
        self.mergers = []
        self.param_widget = None

        # Create UI
        self.create_buttons()
        self.create_holes()
        self.load_assets()
        
        # Measurements
        self.measurements = {
            "Current": 0.0,
            "Voltage": 0.0,
            "Resistance": 0.0,
            "Power": 0.0
        }
    def load_assets(self):
        try:
            self.component_images = {
                "Battery": pygame.image.load(r"assets\Battery.png"),
                "Resistor": pygame.image.load(r"assets\Resistor.png"),
                "LED": pygame.image.load(r"assets\LED.png")
            }
        except FileNotFoundError:
            self.component_images = {
                "Battery": pygame.image.load(r"CircuitSim\assets\Battery.png"),
                "Resistor": pygame.image.load(r"CircuitSim\assets\Resistor.png"),
                "LED": pygame.image.load(r"CircuitSim\assets\LED.png")
            }
    def get_hole_pos(self, row, col):
        # Find hole by row/col
        for hole in self.holes:
            if hole.row == row and hole.col == col:
                return (hole.x, hole.y)
        return (0, 0)
    def draw_component(self, component):
        start_pos = self.get_hole_pos(*component.node1)
        end_pos = self.get_hole_pos(*component.node2)
        
        # Calculate midpoint, length, angle
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = (start_pos[1] + end_pos[1]) / 2
        
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = (dx**2 + dy**2)**0.5
        angle = math.degrees(math.atan2(-dy, dx)) + 180

        # Draw wire/leads
        if component.name == "Wire":
            pygame.draw.line(self.screen, (50, 50, 50), start_pos, end_pos, 4)
            return

        # For other components draw leads to a central area
        body_length = 40
        if length > body_length:
            scale = (length - body_length) / 2 / length
            lead1_end = (start_pos[0] + dx * scale, start_pos[1] + dy * scale)
            lead2_start = (end_pos[0] - dx * scale, end_pos[1] - dy * scale)
            
            pygame.draw.line(self.screen, (150, 150, 150), start_pos, lead1_end, 2)
            pygame.draw.line(self.screen, (150, 150, 150), lead2_start, end_pos, 2)
        
        # Draw the component
        image = self.component_images.get(component.name, None)
        
        if image:
            # Scale image to fit standard component size
            scaled_image = pygame.transform.scale(image, (body_length, 20))
            
            # Rotate and center image
            rotated_image = pygame.transform.rotate(scaled_image, angle)
            rect = rotated_image.get_rect(center=(mid_x, mid_y))
            self.screen.blit(rotated_image, rect)
        else:
            # Fallback drawing
            self.draw_fallback_component(component, mid_x, mid_y, angle, body_length)
    def draw_fallback_component(self, component, x, y, angle, length):
        # Create a surface for the component body to easily rotate it
        surf = pygame.Surface((length, 20), pygame.SRCALPHA)
        
        color = (200, 200, 200) # Default
        label = ""
        
        if component.name == "Battery":
            color = (50, 50, 50)
            label = f"{component.voltage}V"
            # Draw battery symbol simplified (just a box for now)
            pygame.draw.rect(surf, color, (0, 0, length, 20), border_radius=4)
            # Polarity visual
            pygame.draw.rect(surf, (200, 200, 200), (4, 4, length-8, 12)) 
            pygame.draw.line(surf, (0,0,0), (length//2 - 5, 10), (length//2 + 5, 10), 2) # Minus
            pygame.draw.line(surf, (0,0,0), (length//2, 5), (length//2, 15), 2) # Plus (vertical part)

        elif component.name == "Resistor":
            color = (210, 180, 140)
            label = f"{component.resistance}"
            pygame.draw.rect(surf, color, (0, 0, length, 20), border_radius=5)
            pygame.draw.rect(surf, (255, 0, 0), (10, 0, 5, 20))
            pygame.draw.rect(surf, (0, 255, 0), (20, 0, 5, 20))

        elif component.name == "LED":
            c_map = {"red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255), 
                     "yellow": (255, 255, 0), "white": (255, 255, 255)}
            led_c = c_map.get(getattr(component, 'color', 'red'), (255, 0, 0))
            label = ""
            pygame.draw.ellipse(surf, led_c, (5, 0, length-10, 20))

        # Rotate and blit
        rotated_surf = pygame.transform.rotate(surf, angle)
        rect = rotated_surf.get_rect(center=(x, y))
        self.screen.blit(rotated_surf, rect)
        
        # Draw label near component (not rotated for readability)
        if label:
            text = self.small_font.render(str(label), True, (0, 0, 0))
            self.screen.blit(text, (x - 10, y - 25))
    def create_buttons(self):
        # Component buttons
        self.buttons = []
        componentsList = [Wire, Battery, Resistor, LED]
        component_text = ["Wire", "Battery", "Resistor", "LED"]
        for i, comp in enumerate(component_text):
            btn = Button(50 + i * 130, 30, 120, 45, comp, componentsList[i])
            if comp == self.active_component_txt:
                btn.selected = True
            self.buttons.append(btn)
        self.run_button = Button(570, 30, 120, 45, "Run", None)
    def open_param_widget_for(self, btn):
        # Anchor directly below the clicked button
        anchor_x = btn.rect.x
        anchor_y = btn.rect.bottom + 6
        self.param_button_rect = btn.rect

        if btn.text == "Battery":
            # Create numeric counter for voltage
            widget = NumericCounter(anchor_x + 80, anchor_y, 80, 30,
                                    label="Voltage", value=9, step=1, min_val=1, max_val=100000000)
            widget.set_position(anchor_x + 80, anchor_y)
            self.param_widget = widget
            self.param_for = "Battery"
            # Create instance with current value
            self.active_component = Battery(0, 0, None, None, widget.value)

        elif btn.text == "Resistor":
            # Create numeric counter for resistance
            widget = NumericCounter(anchor_x + 80, anchor_y, 100, 30,
                                    label="Resistance", value=330, step=10, min_val=1, max_val=100000)
            widget.set_position(anchor_x + 80, anchor_y)
            self.param_widget = widget
            self.param_for = "Resistor"
            self.active_component = Resistor(0, 0, None, None, widget.value, 0.0)

        elif btn.text == "LED":
            # Create dropdown for LED color
            widget = Dropdown(anchor_x + 80, anchor_y, 100, 30,
                              label="Color", options=["red","green","blue","yellow","white"], default="red")
            widget.set_position(anchor_x + 80, anchor_y)
            self.param_widget = widget
            self.param_for = "LED"
            self.active_component = LED(0, 0, None, None, 220, 0.0, widget.selected_option)  # default 220Ω
        else:
            self.param_widget = None
            self.param_for = None
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
        
        self.init_node_system()
    def init_node_system(self):
        self.uf = UnionFind(self.holes)
        
        for row in [0, 1]:
            holes = [h for h in self.holes if h.row == row]
            for i in range(len(holes) - 1):
                self.uf.union(holes[i], holes[i+1])
                
        for row in [13, 14]:
            holes = [h for h in self.holes if h.row == row]
            for i in range(len(holes) - 1):
                self.uf.union(holes[i], holes[i+1])
        
        for col in range(40):
            # Top section
            top_col_holes = [h for h in self.holes if 2 <= h.row <= 6 and h.col == col]
            for i in range(len(top_col_holes) - 1):
                self.uf.union(top_col_holes[i], top_col_holes[i+1])
                
            # Bottom section
            bot_col_holes = [h for h in self.holes if 8 <= h.row <= 12 and h.col == col]
            for i in range(len(bot_col_holes) - 1):
                self.uf.union(bot_col_holes[i], bot_col_holes[i+1])
        
        # Helper to find a hole at coords
        def get_h(r, c):
            return next((h for h in self.holes if h.row == r and h.col == c), None)

        # Row 0 -> ID 0
        h = get_h(0, 0)
        if h: self.uf.set_id(h, 0)
        
        # Row 1 -> ID 1
        h = get_h(1, 0)
        if h: self.uf.set_id(h, 1)

        # Top Columns -> 2..41
        for col in range(40):
            h = get_h(2, col)
            if h: self.uf.set_id(h, 2 + col)
            
        # Bottom Columns -> 42..81
        for col in range(40):
            h = get_h(8, col)
            if h: self.uf.set_id(h, 42 + col)
            
        # Row 13 -> ID 82
        h = get_h(13, 0)
        if h: self.uf.set_id(h, 82)
        
        # Row 14 -> ID 83
        h = get_h(14, 0)
        if h: self.uf.set_id(h, 83)

        self.sync_node_ids()
    def sync_node_ids(self):
        # Update every hole's local node_id property from the UF system
        for hole in self.holes:
            hole.node_id = self.uf.get_id(hole)    
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

        # Draw components
        for component in self.components:
            self.draw_component(component)
        for merger in self.mergers:
            self.draw_component(merger)
        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.screen, self.font)
        self.run_button.draw(self.screen, self.font)
    def handle_click(self, pos):
        if self.param_widget:
            # Check for outside click logic
            bounds = self.param_widget.bounds()
            clicked_outside = not bounds.collidepoint(pos)

            val = self.param_widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos))
            if val is not None:
                self.update_active_component_param(val)
                if not clicked_outside:
                    return

            # close if clicked outside
            if clicked_outside:
                if isinstance(self.param_widget, Dropdown):
                    self.param_widget.expanded = False
                self.param_widget = None
                self.param_for = None


        # Check buttons
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                for b in self.buttons:
                    b.selected = False
                btn.selected = True
                self.active_component_txt = btn.text
                if btn.text == "Wire":
                    self.active_component = Wire(0, 0)
                    self.param_widget = None
                    self.param_for = None
                else:
                    self.open_param_widget_for(btn)
                return

        if self.run_button.rect.collidepoint(pos):
            print("Running simulation...")
            print("Current components: " + ", ".join(c.name + " [Node " + str(c.node_id_1) + " -> " + str(c.node_id_2) + "]" for c in self.components))
            active_nodes = list(set([c.node_id_1 for c in self.components] + [c.node_id_2 for c in self.components]))
            print("Active nodes: " + ", ".join(str(n) for n in active_nodes))
            matrix = generate_incidence_matrix(self.components, active_nodes)
            print("Incidence Matrix:")
            for row in matrix:
                print(row)
            print("Modified Nodal Analysis:")
            voltages, currents = ModifiedNodalAnalysis(matrix, self.components, active_nodes)
            print("Voltages:", voltages)
            print("Voltages:", ", ".join(component.name + " - " + str(component.voltage_drop) + "V" for component in self.components if component.name != "Battery"))
            print("Currents:", currents)
            return
        
        # Check holes for placement
        for hole in self.holes:
            if hole.contains(pos):
                if self.first_hole is None:
                    if isinstance(self.active_component, Battery):
                        if hole == self.holes[0]:
                            self.uf.set_id(hole, 0)
                            self.sync_node_ids()
                        else:
                            prev_id = hole.node_id
                            self.uf.set_id(hole, 0)
                            self.uf.set_id(self.holes[0], prev_id)
                            self.sync_node_ids()
                    self.first_hole = hole
                    self.active_component.node_id_1 = hole.node_id
                    print(f"Start: row={hole.row}, col={hole.col}, rail={hole.is_rail} [Node {hole.node_id}]")
                else:
                    self.active_component.node1 = (self.first_hole.row, self.first_hole.col)
                    self.active_component.node2 = (hole.row, hole.col)
                    self.active_component.node_id_2 = hole.node_id
                    if isinstance(self.active_component, Wire):
                        self.mergers.append(self.active_component)
                        # Connect the nodes in UnionFind
                        prev_id = max(self.first_hole.node_id, hole.node_id)
                        target_id = min(self.first_hole.node_id, hole.node_id)
                        self.uf.union(self.first_hole, hole)
                        self.uf.set_id(self.first_hole, target_id)
                        self.sync_node_ids()
                        for component in self.components:
                            if component.node_id_1 == prev_id:
                                component.node_id_1 = target_id
                            if component.node_id_2 == prev_id:
                                component.node_id_2 = target_id
                    else:
                        self.components.append(self.active_component)
                    print(f"End: row={hole.row}, col={hole.col}, rail={hole.is_rail} [Node {hole.node_id}]")
                    print(f"Placing {self.active_component.name}")
                    print("Current components: " + ", ".join(c.name for c in self.components))
                    
                    # Refresh active component so we don't reuse the same object
                    if isinstance(self.active_component, Wire):
                        self.active_component = Wire(0, 0)
                    elif isinstance(self.active_component, Battery):
                        self.active_component = Battery(0, 0, None, None, self.active_component.voltage)
                    elif isinstance(self.active_component, Resistor):
                        self.active_component = Resistor(0, 0, None, None, self.active_component.resistance, 0.0)
                    elif isinstance(self.active_component, LED):
                        self.active_component = LED(0, 0, None, None, 220, 0.0, self.active_component.color)
                        
                    self.first_hole = None
                return 
    def update_active_component_param(self, value):
        if self.active_component_txt == "Battery":
             self.active_component = Battery(0, 0, None, None, value)
        elif self.active_component_txt == "Resistor":
             self.active_component = Resistor(0, 0, None, None, value, 0.0)
        elif self.active_component_txt == "LED":
             self.active_component = LED(0, 0, None, None, 220, 0.0, value)

    def run(self):
        # Main loop
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if self.param_widget:
                        value = self.param_widget.handle_event(event)
                        if value is not None:
                            self.update_active_component_param(value)
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
                                self.active_component = Resistor(0, 0, value, 0.0)
                            elif self.active_component_txt == "LED":
                                self.active_component = LED(0, 0, 220, 0.0, value)
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

# Run the simulator
if __name__ == "__main__":
    app = BreadboardSimulator()
    app.run()