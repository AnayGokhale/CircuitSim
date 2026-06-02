import asyncio
import numpy  # must be imported first for pygbag
import pygame
import sys
import math
from Components import Wire, Battery, Resistor, Capacitor, Inductor, LED
from Physics import generate_incidence_matrix, ModifiedNodalAnalysis, calculate_time_constant
# Initialize Pygame
pygame.init()

if sys.platform == "emscripten":
    import platform as _platform
    _platform.window.canvas.style.width = "100vw"
    _platform.window.canvas.style.height = "100vh"
    _platform.window.canvas.style.position = "fixed"
    _platform.window.canvas.style.top = "0"
    _platform.window.canvas.style.left = "0"
    _platform.window.document.body.style.margin = "0"
    _platform.window.document.body.style.overflow = "hidden"

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

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
BREADBOARD_COLOR = (255, 255, 255)
HOLE_SIZE = 8
HOLE_COLOR = (40, 40, 40)
HOLE_SPACING = 20
BG_COLOR = (248, 249, 250) # Light Grey
PANEL_COLOR = (255, 255, 255)
BUTTON_COLOR = (59, 130, 246)
BUTTON_HOVER = (96, 165, 250)
BUTTON_SELECTED = (37, 99, 235)
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
        self.occupied = False
        
    def draw(self, surface, color=HOLE_COLOR):
        pygame.draw.circle(surface, color, (self.x, self.y), self.radius)
        
    def contains(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx*dx + dy*dy <= (self.radius + 5)**2

class Button:
# UI Button for component selection 
    def __init__(self, x, y, width, height, text, type, symbol=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.type = type
        self.selected = False
        self.symbol = symbol
        
    def draw(self, surface, font, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        color = BUTTON_SELECTED if self.selected else BUTTON_COLOR
        if not self.selected and self.rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER
            
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        
        if self.symbol:
            self.draw_symbol(surface, font)
        else:
            text_surf = font.render(self.text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

    def draw_symbol(self, surface, font):
        cx, cy = self.rect.center
        white = (255, 255, 255)
        
        if self.symbol == 'play':
            size = 10
            points = [(cx - size//2 + 2, cy - size + 2), (cx - size//2 + 2, cy + size - 2), (cx + size - 2, cy)]
            pygame.draw.polygon(surface, white, points)
            
        elif self.symbol == 'pause':
            w, h = 4, 14
            gap = 6
            pygame.draw.rect(surface, white, (cx - gap//2 - w, cy - h//2, w, h))
            pygame.draw.rect(surface, white, (cx + gap//2, cy - h//2, w, h))
            
        elif self.symbol == 'back10':
            size = 8
            p1 = [(cx - 2, cy - size), (cx - 2, cy + size), (cx - 10, cy)]
            p2 = [(cx + 6, cy - size), (cx + 6, cy + size), (cx - 2, cy)]
            pygame.draw.polygon(surface, white, p1)
            pygame.draw.polygon(surface, white, p2)
            
            small_font = pygame.font.Font(None, 18)
            t_surf = small_font.render("10", True, white)
            surface.blit(t_surf, (cx - 7, cy + 5))
            
        elif self.symbol == 'fwd10':
            size = 8
            p1 = [(cx - 10, cy - size), (cx - 10, cy + size), (cx - 2, cy)]
            p2 = [(cx - 2, cy - size), (cx - 2, cy + size), (cx + 6, cy)]
            pygame.draw.polygon(surface, white, p1)
            pygame.draw.polygon(surface, white, p2)
            
            small_font = pygame.font.Font(None, 18)
            t_surf = small_font.render("10", True, white)
            surface.blit(t_surf, (cx - 3, cy + 5))
            
        elif self.symbol == 'reset':
            size = 12
            pygame.draw.rect(surface, white, (cx - size//2, cy - size//2, size, size))

class NumericCounter:
    def __init__(self, x, y, width, height, label, value=0.0, step=1.0, min_val=0.0, max_val=1000.0):
        self.rect = pygame.Rect(x, y, width, height)
        self.value = float(value)
        self.step = float(step)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
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
        left = self.minus_rect.x - 100
        top = self.rect.y
        right = self.plus_rect.right
        bottom = self.rect.bottom
        return pygame.Rect(left, top, right - left, bottom - top)

    def draw(self, surface, font, mouse_pos=None):
        label_surf = font.render(self.label, True, (0,0,0))
        label_y = self.rect.centery - label_surf.get_height() // 2
        label_x = self.minus_rect.left - 15 - label_surf.get_width()
        surface.blit(label_surf, (label_x, label_y))

        bg_color = (255, 255, 255) if self.active else (230, 230, 230)
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=4)
        if self.active:
            pygame.draw.rect(surface, (0, 100, 255), self.rect, 2, border_radius=4)


        display_text = self.text if self.active else f"{self.value:.2f}".rstrip('0').rstrip('.')
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
                self.text = f"{self.value:.2f}".rstrip('0').rstrip('.')
                return self.value
            elif self.plus_rect.collidepoint(event.pos):
                self.value = min(self.max_val, self.value + self.step)
                self.text = f"{self.value:.2f}".rstrip('0').rstrip('.')
                return self.value
            elif self.rect.collidepoint(event.pos):
                self.active = True
                self.text = f"{self.value:.2f}".rstrip('0').rstrip('.')
            else:
                if self.active:
                    try:
                        val = float(self.text)
                        self.value = min(self.max_val, max(self.min_val, val))
                    except ValueError:
                        pass
                    self.text = f"{self.value:.2f}".rstrip('0').rstrip('.')
                    self.active = False
                    return self.value
                self.active = False
                self.text = f"{self.value:.2f}".rstrip('0').rstrip('.')

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                try:
                    val = float(self.text)
                    self.value = min(self.max_val, max(self.min_val, val))
                except ValueError:
                     pass
                self.text = f"{self.value:.2f}".rstrip('0').rstrip('.')
                self.active = False
                return self.value
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                char = event.unicode
                if event.key == pygame.K_KP0: char = '0'
                elif event.key == pygame.K_KP1: char = '1'
                elif event.key == pygame.K_KP2: char = '2'
                elif event.key == pygame.K_KP3: char = '3'
                elif event.key == pygame.K_KP4: char = '4'
                elif event.key == pygame.K_KP5: char = '5'
                elif event.key == pygame.K_KP6: char = '6'
                elif event.key == pygame.K_KP7: char = '7'
                elif event.key == pygame.K_KP8: char = '8'
                elif event.key == pygame.K_KP9: char = '9'
                elif event.key == pygame.K_KP_PERIOD: char = '.'
                elif event.key == pygame.K_KP_MINUS: char = '-'
                
                if char.isdigit() or (char == '.' and '.' not in self.text) or (char == '-' and '-' not in self.text and len(self.text) == 0):
                    self.text += char
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

    def draw(self, surface, font, mouse_pos=None):
        # Label
        label_surf = font.render(self.label, True, (0,0,0))
        surface.blit(label_surf, (self.rect.x - 80, self.rect.y + 5))

        # Main box
        pygame.draw.rect(surface, (230,230,230), self.rect, border_radius=4)
        pygame.draw.rect(surface, (100,100,100), self.rect, 2, border_radius=4)
        text_surf = font.render(str(self.selected_option), True, (0,0,0))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))
        
        # Dropdown arrow
        chev_x = self.rect.right - 12
        chev_y = self.rect.centery
        pygame.draw.polygon(surface, (100,100,100), [(chev_x - 4, chev_y - 2), (chev_x + 4, chev_y - 2), (chev_x, chev_y + 3)])

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

class UnitDropdown(Dropdown):
    def __init__(self, x, y, width, height, options, default):
        super().__init__(x, y, width, height, "", options, default)
        
    def draw(self, surface, font, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        # Main box
        pygame.draw.rect(surface, (210,210,210), self.rect, border_radius=4)
        text_surf = font.render(str(self.selected_option), True, (0,0,0))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

        if self.expanded:
            for i, opt in enumerate(self.options):
                opt_rect = self.option_rect(i)
                pygame.draw.rect(surface, (200,200,200), opt_rect)
                if opt_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(surface, (180,180,180), opt_rect)
                opt_surf = font.render(str(opt), True, (0,0,0))
                surface.blit(opt_surf, opt_surf.get_rect(center=opt_rect.center))


def _fmt2(val):
    return f"{val:.2f}".rstrip('0').rstrip('.')

def format_si(value, unit, decimals=2):
    if value == 0:
        return f"0 {unit}"
    
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    
    # Clamp pico-level (and any smaller noise) to zero
    if abs_val < 1e-9:
        return f"0 {unit}"
    elif abs_val < 1e-6:
        return f"{sign}{_fmt2(abs_val*1e9)} n{unit}"
    elif abs_val < 1e-3:
        return f"{sign}{_fmt2(abs_val*1e6)} µ{unit}"
    elif abs_val < .1:
        return f"{sign}{_fmt2(abs_val*1e3)} m{unit}"
    elif abs_val >= 1e9:
        return f"{sign}{_fmt2(abs_val/1e9)} G{unit}"
    elif abs_val >= 1e6:
        return f"{sign}{_fmt2(abs_val/1e6)} M{unit}"
    elif abs_val >= 1e3:
        return f"{sign}{_fmt2(abs_val/1e3)} k{unit}"
    else:
        return f"{sign}{_fmt2(abs_val)} {unit}"


class SidePanel:
    def __init__(self, x, y, width, height, simulator):
        self.rect = pygame.Rect(x, y, width, height)
        self.component = None
        self.visible = False
        self.simulator = simulator
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 32)
        
    def set_component(self, component):
        self.component = component
        self.visible = True
        
    def draw(self, surface):
        if not self.visible or not self.component:
            return
            
        # Draw panel background
        pygame.draw.rect(surface, PANEL_COLOR, self.rect, border_radius=10)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=10)
        
        # Title
        title = self.component.name
        title_surf = self.title_font.render(title, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 20, self.rect.y + 20))
        
        y_offset = 60
        line_height = 30
        
        def draw_text(text, val_color=(0,0,0)):
            nonlocal y_offset
            surf = self.font.render(text, True, val_color)
            surface.blit(surf, (self.rect.x + 20, self.rect.y + y_offset))
            y_offset += line_height

        # Properties based on type
        if isinstance(self.component, Resistor):
            draw_text(f"Resistance: {format_si(self.component.resistance, chr(0x2126))}")
            if self.simulator.is_simulating or self.simulator.sim_paused:
                draw_text(f"Voltage Drop: {format_si(self.component.voltage_drop, 'V')}")
                draw_text(f"Current: {format_si(self.component.current, 'A')}")
            
        elif isinstance(self.component, Capacitor):
            draw_text(f"Capacitance: {format_si(self.component.capacitance, 'F')}")
            if self.simulator.is_simulating or self.simulator.sim_paused:
                draw_text(f"Voltage Drop: {format_si(self.component.voltage_drop, 'V')}")
                draw_text(f"Current: {format_si(self.component.current, 'A')}")
                charge = self.component.capacitance * self.component.voltage_drop
                draw_text(f"Charge: {format_si(charge, 'C')}")
                tau = self.simulator.current_tau
                has_lc = any(isinstance(c, Inductor) for c in self.simulator.components) and any(isinstance(c, Capacitor) for c in self.simulator.components)
                if has_lc and tau:
                    import math
                    period = 2 * math.pi * tau
                    freq = 1.0 / period
                    draw_text(f"Period: {format_si(period, 's')}")
                    draw_text(f"Frequency: {format_si(freq, 'Hz')}")
                else:
                    if tau:
                        draw_text(f"\u03c4: {format_si(tau, 's')}")
                    else:
                        draw_text(f"\u03c4: Does not Exist")

        elif isinstance(self.component, Inductor):
            draw_text(f"Inductance: {format_si(self.component.inductance, 'H')}")
            if self.simulator.is_simulating or self.simulator.sim_paused:
                draw_text(f"Voltage Drop: {format_si(self.component.voltage_drop, 'V')}")
                draw_text(f"Current: {format_si(self.component.current, 'A')}")
                energy = 0.5 * self.component.inductance * self.component.current ** 2
                draw_text(f"Energy: {format_si(energy, 'J')}")
                tau = self.simulator.current_tau
                has_lc = any(isinstance(c, Inductor) for c in self.simulator.components) and any(isinstance(c, Capacitor) for c in self.simulator.components)
                if has_lc and tau:
                    import math
                    period = 2 * math.pi * tau
                    freq = 1.0 / period
                    draw_text(f"Period: {format_si(period, 's')}")
                    draw_text(f"Frequency: {format_si(freq, 'Hz')}")
                else:
                    if tau:
                        draw_text(f"\u03c4: {format_si(tau, 's')}")
                    else:
                        draw_text(f"\u03c4: Does not Exist")
            
        elif isinstance(self.component, Battery):
            draw_text(f"Voltage: {format_si(self.component.voltage, 'V')}")
            if self.simulator.is_simulating or self.simulator.sim_paused:
                draw_text(f"Current: {format_si(abs(self.component.current), 'A')}")
            
        elif isinstance(self.component, LED):
            c_map_rev = {v: k for k, v in {"red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255), 
                     "orange": (255, 165, 0)}.items()}
            # self.component.color is a string name
            draw_text(f"Color: {self.component.color}")
            if self.simulator.is_simulating or self.simulator.sim_paused:
                draw_text(f"Voltage Drop: {format_si(self.component.voltage_drop, 'V')}")
                draw_text(f"Current: {format_si(self.component.current, 'A')}")
                
                # Brightness 
                b_val = getattr(self.component, 'brightness', 0)
                if b_val <= 100:
                    draw_text(f"Brightness: {b_val:.1f}%")
                else:
                    draw_text(f"Brightness: {b_val:.1f}% (BURNOUT)", (255, 0, 0))
                
                # Draw a purity bar for brightness
                bar_rect = pygame.Rect(self.rect.x + 20, self.rect.y + y_offset, self.rect.width - 40, 10)
                pygame.draw.rect(surface, (50, 50, 50), bar_rect)
                fill_width = (min(b_val, 100) / 100.0) * (self.rect.width - 40)
                
                # Use LED color for the bar
                c_map = {"red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255), 
                         "orange": (255, 165, 0)}
                bar_color = c_map.get(self.component.color, (255, 255, 255))
                
                if fill_width > 0:
                    pygame.draw.rect(surface, bar_color, (bar_rect.x, bar_rect.y, fill_width, 10))
                y_offset += 20
            
        elif isinstance(self.component, Wire):
            if self.simulator.is_simulating or self.simulator.sim_paused:
                draw_text("Connected Current:")
                
                connected_comps = getattr(self.component, 'connected_components', [])
                # Filter out batteries
                non_batteries = [c for c in connected_comps if not isinstance(c, Battery)]
                
                target_comp = None
                if len(non_batteries) == 1:
                    target_comp = non_batteries[0]
                elif len(non_batteries) > 1:
                    # Prefer component at node1
                    # component nodes are tuples (r, c)
                    w_start = self.component.node1
                    
                    # Check if any component shares this exact start node
                    start_matches = [c for c in non_batteries if c.node1 == w_start or c.node2 == w_start]
                    
                    if start_matches:
                        target_comp = start_matches[0]
                    else:
                        # Just take the first one
                        target_comp = non_batteries[0]
                
                if target_comp:
                    val = getattr(target_comp, 'current', 0)
                    draw_text(f"{target_comp.name}: {format_si(val, 'A')}")
                else:
                    draw_text("N/A", (100, 100, 100))
                    
                y_offset += 10
            draw_text("Connections:", (0,0,0))
            for comp in getattr(self.component, 'connected_components', []):
                 draw_text(f"- {comp.name}", (100, 100, 100))
        
        # Connection Nodes info
        y_offset += 10
        draw_text(f"Nodes: {self.component.node_id_1} <-> {self.component.node_id_2}", (150, 150, 150))


class TutorialManager:
    def __init__(self, simulator):
        self.sim = simulator
        self.active = False
        self.current_step_index = 0
        self.is_paused = False
        self.cursor_pos = [600.0, 350.0]
        self.click_ripple_radius = 0.0
        self.click_ripple_max = 20.0
        self.click_ripple_pos = None
        self.highlight_rect = None
        self.actions = []
        self.title_text = ""
        self.body_text = ""
        self.original_state = None
        
        # Load fonts
        self.font_title = pygame.font.Font(None, 24)
        self.font_body = pygame.font.Font(None, 20)
        self.font_btn = pygame.font.Font(None, 16)
        
        # Define button bounds inside the card (x=150, y=595, w=700, h=95)
        self.skip_btn_rect = pygame.Rect(735, 607, 100, 26)
        self.back_btn_rect = pygame.Rect(615, 649, 70, 28)
        self.play_btn_rect = pygame.Rect(690, 649, 75, 28)
        self.next_btn_rect = pygame.Rect(770, 649, 65, 28)

    def draw_multiline_text(self, surface, text, rect, font, color):
        words = text.split(' ')
        space_w, space_h = font.size(' ')
        x, y = rect.topleft
        line = []
        for word in words:
            word_w, word_h = font.size(word)
            if x + word_w >= rect.right:
                line_surf = font.render(' '.join(line), True, color)
                surface.blit(line_surf, (rect.x, y))
                line = [word]
                x = rect.x + word_w + space_w
                y += word_h + 2
            else:
                line.append(word)
                x += word_w + space_w
        if line:
            line_surf = font.render(' '.join(line), True, color)
            surface.blit(line_surf, (rect.x, y))

    def get_button_pos(self, text):
        for btn in self.sim.buttons:
            if btn.text == text:
                return btn.rect.center
        if text == "Run" and hasattr(self.sim, "run_button"):
            return self.sim.run_button.rect.center
        elif text == "Reset" and hasattr(self.sim, "sim_reset_button"):
            return self.sim.sim_reset_button.rect.center
        elif text == "Pause" and hasattr(self.sim, "sim_pause_button"):
            return self.sim.sim_pause_button.rect.center
        elif text == "Clear" and hasattr(self.sim, "clear_button"):
            return self.sim.clear_button.rect.center
        elif text == "Undo" and hasattr(self.sim, "undo_button"):
            return self.sim.undo_button.rect.center
        return (600, 350)

    def start_tutorial(self):
        import copy
        self.original_state = {
            'components': copy.deepcopy(self.sim.components),
            'mergers': copy.deepcopy(self.sim.mergers),
            'holes_occupied': [h.occupied for h in self.sim.holes],
            'is_simulating': self.sim.is_simulating,
            'sim_paused': self.sim.sim_paused,
            'sim_time': self.sim.sim_time,
            'selected_component': self.sim.selected_component,
            'side_panel_visible': self.sim.side_panel.visible,
            'side_panel_component': self.sim.side_panel.component
        }
        self.active = True
        self.current_step_index = 0
        self.is_paused = False
        self.cursor_pos = [600.0, 350.0]
        self.click_ripple_radius = 0.0
        self.click_ripple_pos = None
        self.highlight_rect = None
        self.setup_step(0)

    def stop_tutorial(self):
        if not self.active:
            return
        self.active = False
        self.highlight_rect = None
        self.actions = []
        if hasattr(self, 'auto_advance_timer'):
            del self.auto_advance_timer
        if hasattr(self, 'action_wait_timer'):
            del self.action_wait_timer
        
        # Restore original state
        if self.original_state:
            self.sim.components = self.original_state['components']
            self.sim.mergers = self.original_state['mergers']
            for i, occ in enumerate(self.original_state['holes_occupied']):
                self.sim.holes[i].occupied = occ
            self.sim.is_simulating = self.original_state['is_simulating']
            self.sim.sim_paused = self.original_state['sim_paused']
            self.sim.sim_time = self.original_state['sim_time']
            if self.sim.sim_time_widget:
                self.sim.sim_time_widget.value = self.sim.sim_time
                self.sim.sim_time_widget.text = f"{self.sim.sim_time:.2f}".rstrip('0').rstrip('.')
            self.sim.selected_component = self.original_state['selected_component']
            self.sim.side_panel.visible = self.original_state['side_panel_visible']
            self.sim.side_panel.component = self.original_state['side_panel_component']
            self.sim.rebuild_circuit()
            self.original_state = None

    def setup_step(self, step_idx):
        self.sim.is_simulating = False
        self.sim.sim_paused = False
        self.sim.sim_time = 0.0
        if self.sim.sim_time_widget:
            self.sim.sim_time_widget.value = 0.0
            self.sim.sim_time_widget.text = "0.0"
        
        self.sim.components.clear()
        self.sim.mergers.clear()
        for h in self.sim.holes:
            h.occupied = False
        self.sim.first_hole = None
        self.sim.selected_component = None
        self.sim.side_panel.visible = False
        self.sim.side_panel.component = None

        def place_comp(comp_class, r1, c1, r2, c2, *args):
            h1 = self.sim.get_hole_by_node((r1, c1))
            h2 = self.sim.get_hole_by_node((r2, c2))
            if h1 and h2:
                h1.occupied = True
                h2.occupied = True
                if comp_class == Wire:
                    comp = Wire((r1, c1), (r2, c2))
                    self.sim.mergers.append(comp)
                else:
                    comp = comp_class((r1, c1), (r2, c2), h1.node_id, h2.node_id, *args)
                    self.sim.components.append(comp)

        if step_idx >= 2:
            place_comp(Battery, 2, 5, 2, 10, 9.0)
        if step_idx >= 3:
            place_comp(Resistor, 3, 10, 3, 15, 500, 0.0)
        if step_idx >= 4:
            place_comp(LED, 4, 15, 4, 20, 220, 0.0, "red")
        if step_idx >= 5:
            place_comp(Wire, 5, 20, 5, 5)

        self.sim.rebuild_circuit()

        if step_idx >= 6:
            self.sim.is_simulating = True
            self.sim.sim_paused = False
            active_nodes = list(set([c.node_id_1 for c in self.sim.components] + [c.node_id_2 for c in self.sim.components]))
            try:
                matrix = generate_incidence_matrix(self.sim.components, active_nodes)
                ModifiedNodalAnalysis(matrix, self.sim.components, active_nodes, dt=0.01)
            except Exception:
                pass
        
        if step_idx >= 7:
            if self.sim.components:
                resistor = next((c for c in self.sim.components if isinstance(c, Resistor)), None)
                if resistor:
                    self.sim.selected_component = resistor
                    self.sim.side_panel.set_component(resistor)

        if hasattr(self, 'auto_advance_timer'):
            del self.auto_advance_timer
        if hasattr(self, 'action_wait_timer'):
            del self.action_wait_timer
        self.init_actions_for_step(step_idx)

    def init_actions_for_step(self, step_idx):
        self.actions = []
        self.highlight_rect = None
        
        if step_idx == 0:
            self.actions.append({"type": "text", "title": "Welcome to CircuitSim!", "text": "This walkthrough will guide you through all features of the simulator by building a working circuit. Let's get started!"})
            self.actions.append({"type": "wait", "duration": 2.0})
            
        elif step_idx == 1:
            btn_pos = self.get_button_pos("Battery")
            h1_pos = self.sim.get_hole_pos(2, 5)
            h2_pos = self.sim.get_hole_pos(2, 10)
            btn = next((b for b in self.sim.buttons if b.text == "Battery"), None)
            
            self.actions.append({"type": "text", "title": "Step 1: Adding a Power Source", "text": "First, select the 'Battery' tool. Notice the parameter configuration options that appear below the button. We'll place the battery terminals from row 2, col 5 to col 10."})
            if btn:
                self.actions.append({"type": "highlight", "rect": btn.rect})
            self.actions.append({"type": "move", "pos": btn_pos})
            self.actions.append({"type": "click", "pos": btn_pos})
            self.actions.append({"type": "wait", "duration": 0.5})
            self.actions.append({"type": "highlight_param"})
            self.actions.append({"type": "wait", "duration": 1.0})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h1_pos[0]-10, h1_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h1_pos})
            self.actions.append({"type": "click", "pos": h1_pos})
            self.actions.append({"type": "wait", "duration": 0.3})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h2_pos[0]-10, h2_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h2_pos})
            self.actions.append({"type": "click", "pos": h2_pos})
            self.actions.append({"type": "wait", "duration": 1.0})

        elif step_idx == 2:
            btn_pos = self.get_button_pos("Resistor")
            h1_pos = self.sim.get_hole_pos(3, 10)
            h2_pos = self.sim.get_hole_pos(3, 15)
            btn = next((b for b in self.sim.buttons if b.text == "Resistor"), None)
            
            self.actions.append({"type": "text", "title": "Step 2: Protecting the Circuit", "text": "Select the 'Resistor' tool. Resistors limit current flow to protect components. Let's adjust its value to 500 ohms using the parameter plus button, and place it from row 3, col 10 to col 15."})
            if btn:
                self.actions.append({"type": "highlight", "rect": btn.rect})
            self.actions.append({"type": "move", "pos": btn_pos})
            self.actions.append({"type": "click", "pos": btn_pos})
            self.actions.append({"type": "wait", "duration": 0.5})
            self.actions.append({"type": "highlight_param"})
            
            # Click plus button twice to go from 300 to 500 (since step is 100)
            plus_pos = lambda: self.sim.param_widget.plus_rect.center if (self.sim.param_widget and hasattr(self.sim.param_widget, 'plus_rect')) else (460, 96)
            self.actions.append({"type": "move", "pos": plus_pos})
            self.actions.append({"type": "click", "pos": plus_pos})
            self.actions.append({"type": "wait", "duration": 0.4})
            self.actions.append({"type": "click", "pos": plus_pos})
            self.actions.append({"type": "wait", "duration": 0.5})
            
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h1_pos[0]-10, h1_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h1_pos})
            self.actions.append({"type": "click", "pos": h1_pos})
            self.actions.append({"type": "wait", "duration": 0.3})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h2_pos[0]-10, h2_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h2_pos})
            self.actions.append({"type": "click", "pos": h2_pos})
            self.actions.append({"type": "wait", "duration": 1.0})

        elif step_idx == 3:
            btn_pos = self.get_button_pos("LED")
            h1_pos = self.sim.get_hole_pos(4, 15)
            h2_pos = self.sim.get_hole_pos(4, 20)
            btn = next((b for b in self.sim.buttons if b.text == "LED"), None)
            
            self.actions.append({"type": "text", "title": "Step 3: Placing the LED", "text": "Select the 'LED' tool. LEDs only conduct electricity in one direction. Place it from row 4, col 15 to col 20. Note that you can configure its color from the parameter menu!"})
            if btn:
                self.actions.append({"type": "highlight", "rect": btn.rect})
            self.actions.append({"type": "move", "pos": btn_pos})
            self.actions.append({"type": "click", "pos": btn_pos})
            self.actions.append({"type": "wait", "duration": 0.5})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h1_pos[0]-10, h1_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h1_pos})
            self.actions.append({"type": "click", "pos": h1_pos})
            self.actions.append({"type": "wait", "duration": 0.3})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h2_pos[0]-10, h2_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h2_pos})
            self.actions.append({"type": "click", "pos": h2_pos})
            self.actions.append({"type": "wait", "duration": 1.0})

        elif step_idx == 4:
            btn_pos = self.get_button_pos("Wire")
            h1_pos = self.sim.get_hole_pos(5, 20)
            h2_pos = self.sim.get_hole_pos(5, 5)
            btn = next((b for b in self.sim.buttons if b.text == "Wire"), None)
            
            self.actions.append({"type": "text", "title": "Step 4: Connecting the Loop", "text": "Select the 'Wire' tool. Wires connect nodes together. Connect row 5, col 20 to col 5 to complete our closed loop: Battery -> Resistor -> LED -> Wire -> Battery."})
            if btn:
                self.actions.append({"type": "highlight", "rect": btn.rect})
            self.actions.append({"type": "move", "pos": btn_pos})
            self.actions.append({"type": "click", "pos": btn_pos})
            self.actions.append({"type": "wait", "duration": 0.5})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h1_pos[0]-10, h1_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h1_pos})
            self.actions.append({"type": "click", "pos": h1_pos})
            self.actions.append({"type": "wait", "duration": 0.3})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(h2_pos[0]-10, h2_pos[1]-10, 20, 20)})
            self.actions.append({"type": "move", "pos": h2_pos})
            self.actions.append({"type": "click", "pos": h2_pos})
            self.actions.append({"type": "wait", "duration": 1.5})

        elif step_idx == 5:
            btn_pos = self.get_button_pos("Run")
            
            self.actions.append({"type": "text", "title": "Step 5: Simulating the Circuit", "text": "The circuit is now complete! Let's click the 'Run' button. The simulation engine computes nodal voltages and currents using Modified Nodal Analysis. Watch the LED glow!"})
            if self.sim.run_button:
                self.actions.append({"type": "highlight", "rect": self.sim.run_button.rect})
            self.actions.append({"type": "move", "pos": btn_pos})
            self.actions.append({"type": "click", "pos": btn_pos})
            self.actions.append({"type": "wait", "duration": 2.0})

        elif step_idx == 6:
            h1_pos = self.sim.get_hole_pos(3, 10)
            h2_pos = self.sim.get_hole_pos(3, 15)
            target_pos = ((h1_pos[0] + h2_pos[0]) // 2, (h1_pos[1] + h2_pos[1]) // 2)
            
            lh1 = self.sim.get_hole_pos(4, 15)
            lh2 = self.sim.get_hole_pos(4, 20)
            led_pos = ((lh1[0] + lh2[0]) // 2, (lh1[1] + lh2[1]) // 2)
            
            self.actions.append({"type": "text", "title": "Step 6: Inspecting Real-Time Data", "text": "Right-click on the Resistor, and then right-click on the LED. The Side Panel displays live diagnostics for each selected component."})
            self.actions.append({"type": "move", "pos": target_pos})
            self.actions.append({"type": "click", "pos": target_pos, "button": 3})
            self.actions.append({"type": "wait", "duration": 1.5})
            self.actions.append({"type": "move", "pos": led_pos})
            self.actions.append({"type": "click", "pos": led_pos, "button": 3})
            self.actions.append({"type": "highlight", "rect": self.sim.side_panel.rect})
            self.actions.append({"type": "wait", "duration": 2.0})

        elif step_idx == 7:
            self.actions.append({"type": "text", "title": "Step 7: Controlling Simulation Time", "text": "When simulating, you can step backward, pause/play, step forward, or reset using the toolbar next to the timer. The timer shows elapsed simulation time."})
            toolbar_rect = pygame.Rect(720, 20, 240, 60)
            self.actions.append({"type": "highlight", "rect": toolbar_rect})
            self.actions.append({"type": "move", "pos": (795, 52)})
            self.actions.append({"type": "wait", "duration": 1.5})
            self.actions.append({"type": "move", "pos": (1090, 52)})
            self.actions.append({"type": "wait", "duration": 2.0})

        elif step_idx == 8:
            undo_pos = self.get_button_pos("Undo")
            clear_pos = self.get_button_pos("Clear")
            
            self.actions.append({"type": "text", "title": "Step 8: Editing Controls", "text": "Use the Undo button to revert your last placement. Use Clear to remove all components and reset the breadboard. Let's see them at the bottom right."})
            self.actions.append({"type": "highlight", "rect": pygame.Rect(1020, 640, 170, 50)})
            self.actions.append({"type": "move", "pos": undo_pos})
            self.actions.append({"type": "wait", "duration": 1.0})
            self.actions.append({"type": "move", "pos": clear_pos})
            self.actions.append({"type": "wait", "duration": 2.0})

        elif step_idx == 9:
            self.actions.append({"type": "text", "title": "Walkthrough Complete!", "text": "That's it! You've learned all the features of CircuitSim. We will restore your previous circuit. Click 'Finish' to start exploring on your own!"})
            self.actions.append({"type": "wait", "duration": 2.0})

    def handle_event(self, event):
        if not self.active:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.skip_btn_rect.collidepoint(pos):
                self.stop_tutorial()
                return True
            elif self.back_btn_rect.collidepoint(pos):
                self.prev_step()
                return True
            elif self.play_btn_rect.collidepoint(pos):
                self.is_paused = not self.is_paused
                return True
            elif self.next_btn_rect.collidepoint(pos):
                self.next_step()
                return True
            return True
            
        elif event.type in [pygame.MOUSEMOTION, pygame.KEYDOWN, pygame.KEYUP]:
            return True
            
        return False

    def prev_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.setup_step(self.current_step_index)

    def next_step(self):
        if self.current_step_index < 9:
            self.current_step_index += 1
            self.setup_step(self.current_step_index)
        else:
            self.stop_tutorial()

    def update(self):
        if not self.active or self.is_paused:
            return
            
        if not self.actions:
            if not hasattr(self, 'auto_advance_timer'):
                self.auto_advance_timer = 2.0
            else:
                self.auto_advance_timer -= 1/60.0
                if self.auto_advance_timer <= 0:
                    del self.auto_advance_timer
                    self.next_step()
            return
            
        action = self.actions[0]
        
        if action["type"] == "text":
            self.title_text = action["title"]
            self.body_text = action["text"]
            self.actions.pop(0)
            
        elif action["type"] == "highlight":
            self.highlight_rect = action["rect"]
            self.actions.pop(0)
            
        elif action["type"] == "highlight_param":
            if self.sim.param_widget:
                bounds = self.sim.param_widget.bounds()
                if self.sim.param_unit_widget:
                    bounds.union_ip(self.sim.param_unit_widget.bounds())
                self.highlight_rect = bounds
            else:
                self.highlight_rect = None
            self.actions.pop(0)
            
        elif action["type"] == "wait":
            if not hasattr(self, 'action_wait_timer'):
                self.action_wait_timer = action["duration"]
            else:
                self.action_wait_timer -= 1/60.0
                if self.action_wait_timer <= 0:
                    del self.action_wait_timer
                    self.actions.pop(0)
                    
        elif action["type"] in ["move", "click"]:
            target = action["pos"]
            if callable(target):
                target = target()
            dx = target[0] - self.cursor_pos[0]
            dy = target[1] - self.cursor_pos[1]
            dist = (dx**2 + dy**2)**0.5
            
            if dist < 4:
                self.cursor_pos = list(target)
                if action["type"] == "click":
                    self.click_ripple_pos = list(target)
                    self.click_ripple_radius = 1.0
                    btn_val = action.get("button", 1)
                    self.sim.handle_click(target, button=btn_val)
                self.actions.pop(0)
            else:
                speed = 6.0
                self.cursor_pos[0] += (dx / dist) * speed
                self.cursor_pos[1] += (dy / dist) * speed
                
        # Hover effect update based on virtual cursor
        self.sim.hovered_hole = None
        for hole in self.sim.holes:
            if hole.contains(self.cursor_pos):
                self.sim.hovered_hole = hole
                break

    def draw(self, surface):
        if not self.active:
            return
            
        if self.highlight_rect:
            pulse = int(4 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.rect(surface, (250, 180, 50), 
                             (self.highlight_rect.x - 4 - pulse//2, 
                              self.highlight_rect.y - 4 - pulse//2, 
                              self.highlight_rect.width + 8 + pulse, 
                              self.highlight_rect.height + 8 + pulse), 
                             3, border_radius=4)
                             
        card_rect = pygame.Rect(150, 595, 700, 95)
        overlay = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (20, 30, 48, 235), (0, 0, card_rect.width, card_rect.height), border_radius=8)
        pygame.draw.rect(overlay, (99, 102, 241, 255), (0, 0, card_rect.width, card_rect.height), width=2, border_radius=8)
        surface.blit(overlay, card_rect.topleft)
        
        title_surf = self.font_title.render(self.title_text, True, (255, 255, 255))
        surface.blit(title_surf, (card_rect.x + 20, card_rect.y + 12))
        
        body_rect = pygame.Rect(card_rect.x + 20, card_rect.y + 36, 440, 54)
        self.draw_multiline_text(surface, self.body_text, body_rect, self.font_body, (226, 232, 240))
        
        m_pos = self.sim.get_internal_pos(pygame.mouse.get_pos())
        
        def draw_card_btn(rect, text, bg_color, hover_color):
            hovered = rect.collidepoint(m_pos)
            color = hover_color if hovered else bg_color
            pygame.draw.rect(surface, color, rect, border_radius=4)
            btn_surf = self.font_btn.render(text, True, (255, 255, 255))
            surface.blit(btn_surf, btn_surf.get_rect(center=rect.center))
            
        draw_card_btn(self.skip_btn_rect, "Skip Tutorial", (239, 68, 68), (248, 113, 113))
        draw_card_btn(self.back_btn_rect, "Back", (107, 114, 128), (156, 163, 175))
        
        play_text = "Pause" if not self.is_paused else "Resume"
        draw_card_btn(self.play_btn_rect, play_text, (59, 130, 246), (96, 165, 250))
        
        next_text = "Finish" if self.current_step_index == 9 else "Next"
        draw_card_btn(self.next_btn_rect, next_text, (16, 185, 129), (52, 211, 153))
        
        if self.click_ripple_pos and self.click_ripple_radius > 0:
            alpha = int(255 * (1 - self.click_ripple_radius / self.click_ripple_max))
            ripple_surf = pygame.Surface((int(self.click_ripple_max*2), int(self.click_ripple_max*2)), pygame.SRCALPHA)
            pygame.draw.circle(ripple_surf, (255, 215, 0, alpha), (int(self.click_ripple_max), int(self.click_ripple_max)), int(self.click_ripple_radius), 2)
            surface.blit(ripple_surf, (int(self.click_ripple_pos[0] - self.click_ripple_max), int(self.click_ripple_pos[1] - self.click_ripple_max)))
            
            self.click_ripple_radius += 1.5
            if self.click_ripple_radius >= self.click_ripple_max:
                self.click_ripple_radius = 0.0
                self.click_ripple_pos = None
                
        cx, cy = int(self.cursor_pos[0]), int(self.cursor_pos[1])
        points = [(cx, cy), (cx + 8, cy + 15), (cx + 12, cy + 12)]
        pygame.draw.polygon(surface, (255, 255, 255), points)
        pygame.draw.polygon(surface, (0, 0, 0), points, 1)


class BreadboardSimulator:
# Main application class
    def __init__(self):
        # Pygame setup
        if sys.platform == "emscripten":
            import platform as _platform
            w = int(_platform.window.innerWidth)
            h = int(_platform.window.innerHeight)
            self.window = pygame.display.set_mode((w, h))
        else:
            self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Breadboard Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.copyright_font = pygame.font.SysFont("arial", 10)
        
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
        self.selected_component = None
        self.is_simulating = False
        self.param_unit_widget = None

        # Simulation state
        self.sim_time = 0.0
        self.current_tau = None
        self.current_dt = 1/60.0
        self.sim_paused = False
        self.sim_time_widget = None

        # Create UI
        self.create_buttons()
        self.create_holes()
        self.load_assets()
        
        self.side_panel = SidePanel(920, 150, 260, 450, self)
        self.tutorial_manager = TutorialManager(self)
        
        # Measurements
        self.measurements = {
            "Current": 0.0,
            "Voltage": 0.0,
            "Resistance": 0.0,
            "Power": 0.0
        }
        self.history = []
        
        # Persistent defaults
        self.component_defaults = {
            "Battery":   {"val": 9.0, "unit": "V"},
            "Resistor":  {"val": 300, "unit": "Ω"},
            "Capacitor": {"val": 10.0, "unit": "µF"},
            "Inductor":  {"val": 10.0, "unit": "mH"},
            "LED":       "red"
        }
    def load_assets(self):
        import os
        # Try multiple path strategies for desktop and web compatibility
        base_dirs = [
            "assets",
            "CircuitSim/assets",
            os.path.join(os.path.dirname(__file__), "assets"),
        ]
        asset_names = ["Battery", "Resistor", "Capacitor", "LED"]
        self.component_images = {}
        for name in asset_names:
            loaded = False
            for base in base_dirs:
                path = f"{base}/{name}.png"
                try:
                    self.component_images[name] = pygame.image.load(path)
                    loaded = True
                    break
                except Exception:
                    continue
            if not loaded:
                self.component_images[name] = None

    def get_hole_pos(self, row, col):
        # Find hole by row/col
        for hole in self.holes:
            if hole.row == row and hole.col == col:
                return (hole.x, hole.y)
        return (0, 0)
    def distance_point_to_segment(self, point, start, end):
        px, py = point
        x1, y1 = start
        x2, y2 = end
        
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return ((px - x1)**2 + (py - y1)**2)**0.5

        t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t))
        
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return ((px - closest_x)**2 + (py - closest_y)**2)**0.5

    def get_component_at_pos(self, pos):
        all_items = self.components + self.mergers
        
        closest_dist = 15
        closest_item = None
        
        for item in all_items:
            start = self.get_hole_pos(*item.node1)
            end = self.get_hole_pos(*item.node2)
            dist = self.distance_point_to_segment(pos, start, end)
            
            if dist < closest_dist:
                closest_dist = dist
                closest_item = item
                
        return closest_item

    def delete_selected_component(self):
        if not self.selected_component:
            return

        self.save_state()

        comp = self.selected_component
        
        # Free holes
        h1 = self.get_hole_by_node(comp.node1)
        h2 = self.get_hole_by_node(comp.node2)
        if h1: h1.occupied = False
        if h2: h2.occupied = False
        
        # Remove from lists
        if comp in self.components:
            self.components.remove(comp)
        if comp in self.mergers:
            self.mergers.remove(comp)
            
        self.selected_component = None
        self.side_panel.visible = False
        self.side_panel.component = None
        
        # Rebuild circuit connectivity
        self.rebuild_circuit()

    def get_hole_by_node(self, node_tuple):
        r, c = node_tuple
        for h in self.holes:
            if h.row == r and h.col == c:
                return h
        return None

    def save_state(self):
        import copy
        state = {
            'board': copy.deepcopy((self.components, self.mergers)),
            'holes_occupied': [h.occupied for h in self.holes]
        }
        if len(self.history) >= 20:
            self.history.pop(0)
        self.history.append(state)

    def undo(self):
        if self.history:
            state = self.history.pop()
            self.components, self.mergers = state['board']
            for i, occ in enumerate(state['holes_occupied']):
                self.holes[i].occupied = occ
            
            self.first_hole = None
            self.selected_component = None
            self.side_panel.visible = False
            self.side_panel.component = None
            
            self.rebuild_circuit()

    def rebuild_circuit(self):
        self.init_node_system()
        
        for wire in self.mergers:
             h1 = self.get_hole_by_node(wire.node1)
             h2 = self.get_hole_by_node(wire.node2)
             if h1 and h2:
                 prev_id = max(h1.node_id, h2.node_id)
                 target_id = min(h1.node_id, h2.node_id)
                 self.uf.union(h1, h2)
                 self.uf.set_id(h1, target_id)
        
        self.sync_node_ids()

        for comp in self.components:
             h1 = self.get_hole_by_node(comp.node1)
             h2 = self.get_hole_by_node(comp.node2)
             if h1: comp.node_id_1 = h1.node_id
             if h2: comp.node_id_2 = h2.node_id

    def get_connected_components(self, wire):
        h1 = self.get_hole_by_node(wire.node1)
        h2 = self.get_hole_by_node(wire.node2)
        
        connected_names = []
        
        if not h1 or not h2:
            return []
            
        target_ids = {h1.node_id, h2.node_id}
        
        connected_comps = []
        
        for comp in self.components:
             if comp.node_id_1 in target_ids or comp.node_id_2 in target_ids:
                 connected_comps.append(comp)
                 
        return list(set(connected_comps))

    def draw_component(self, component):
        start_pos = self.get_hole_pos(*component.node1)
        end_pos = self.get_hole_pos(*component.node2)
        
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = (start_pos[1] + end_pos[1]) / 2
        
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = (dx**2 + dy**2)**0.5
        angle = math.degrees(math.atan2(-dy, dx)) + 180

        if component == self.selected_component:
            if component.name == "Wire":
                pygame.draw.line(self.screen, (255, 255, 0), start_pos, end_pos, 8)
            else:
                 body_length = 40
                 surf = pygame.Surface((length + 10, 30), pygame.SRCALPHA)
                 pygame.draw.rect(surf, (255, 255, 0), (0, 0, length + 10, 30), border_radius=5)
                 rotated_surf = pygame.transform.rotate(surf, angle)
                 rect = rotated_surf.get_rect(center=(mid_x, mid_y))
                 self.screen.blit(rotated_surf, rect)

        if component.name == "Wire":
            pygame.draw.line(self.screen, (50, 50, 50), start_pos, end_pos, 4)
            return

        if component.name == "Resistor":
            self.draw_custom_resistor(component, start_pos, end_pos, mid_x, mid_y, angle, length)
            return

        if component.name == "Battery":
            self.draw_custom_battery(component, start_pos, end_pos, mid_x, mid_y, angle, length)
            return

        if component.name == "Capacitor":
            self.draw_custom_capacitor(component, start_pos, end_pos, mid_x, mid_y, angle, length)
            return

        if component.name == "Inductor":
            self.draw_custom_inductor(component, start_pos, end_pos, mid_x, mid_y, angle, length)
            return

        if component.name == "LED":
            self.draw_custom_led(component, start_pos, end_pos, mid_x, mid_y, angle, length)
            return

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
    def draw_custom_battery(self, component, start_pos, end_pos, mid_x, mid_y, angle, length):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        correct_angle = math.degrees(math.atan2(-dy, dx))
        body_length = 40
        height = 16
        
        if length > body_length:
            scale = (length - body_length) / 2 / length
            lead1_end = (start_pos[0] + dx * scale, start_pos[1] + dy * scale)
            lead2_start = (end_pos[0] - dx * scale, end_pos[1] - dy * scale)
            pygame.draw.line(self.screen, (200, 50, 50), start_pos, lead1_end, 2)
            pygame.draw.line(self.screen, (50, 50, 50), lead2_start, end_pos, 2)
            
        surf = pygame.Surface((body_length + 4, height), pygame.SRCALPHA)
        
        pygame.draw.rect(surf, (30, 30, 30), (0, 0, body_length, height), border_radius=2)
        pygame.draw.rect(surf, (210, 160, 50), (body_length * 0.7, 0, body_length * 0.3, height), border_radius=2)
        pygame.draw.rect(surf, (200, 200, 200), (body_length, height//2 - 3, 3, 6), border_radius=1)
        
        pygame.draw.line(surf, (0, 0, 0), (body_length - 6, height//2), (body_length - 2, height//2), 1)
        pygame.draw.line(surf, (0, 0, 0), (body_length - 4, height//2 - 2), (body_length - 4, height//2 + 2), 1)
        pygame.draw.line(surf, (255, 255, 255), (4, height//2), (8, height//2), 1)
        
        rotated_surf = pygame.transform.rotate(surf, correct_angle)
        rect = rotated_surf.get_rect(center=(mid_x, mid_y))
        self.screen.blit(rotated_surf, rect)

    def draw_custom_resistor(self, component, start_pos, end_pos, mid_x, mid_y, angle, length):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        correct_angle = math.degrees(math.atan2(-dy, dx))
        body_length = 40
        height = 15
        
        if length > body_length:
            scale = (length - body_length) / 2 / length
            lead1_end = (start_pos[0] + dx * scale, start_pos[1] + dy * scale)
            lead2_start = (end_pos[0] - dx * scale, end_pos[1] - dy * scale)
            
            pygame.draw.line(self.screen, (150, 150, 150), start_pos, lead1_end, 2)
            pygame.draw.line(self.screen, (150, 150, 150), lead2_start, end_pos, 2)
        
        surf = pygame.Surface((body_length, height), pygame.SRCALPHA)
         
        body_color = (222, 184, 135)
        
        width = body_length
        
        end_w = width * 0.15
        center_w = width - (2 * end_w)
        
        left_cap_rect = pygame.Rect(0, 0, end_w * 1.5, height)
        pygame.draw.ellipse(surf, body_color, left_cap_rect)
        
        right_cap_rect = pygame.Rect(width - end_w * 1.5, 0, end_w * 1.5, height)
        pygame.draw.ellipse(surf, body_color, right_cap_rect)
        
        center_rect = pygame.Rect(end_w, height*0.1, center_w, height*0.8)
        pygame.draw.rect(surf, body_color, center_rect)
        
        bands = component.get_color_bands(component.resistance)
        band_w = width * 0.08
        
        positions = [0.2, 0.35, 0.5, 0.8]
        
        for i, band_name in enumerate(bands):
            color = RESISTOR_COLORS.get(band_name, (0,0,0))
            bx = width * positions[i]
            rect = pygame.Rect(bx, 0, band_w, height)
            pygame.draw.rect(surf, color, rect)

        rotated_surf = pygame.transform.rotate(surf, correct_angle)
        rect = rotated_surf.get_rect(center=(mid_x, mid_y))
        self.screen.blit(rotated_surf, rect)

    def draw_custom_capacitor(self, component, start_pos, end_pos, mid_x, mid_y, angle, length):
        pygame.draw.line(self.screen, (150, 150, 150), start_pos, (mid_x, mid_y), 2)
        pygame.draw.line(self.screen, (150, 150, 150), end_pos, (mid_x, mid_y), 2)
        
        cyl_w = 18
        cyl_h = 20
        ellipse_h = 8
        
        surf = pygame.Surface((cyl_w, cyl_h + ellipse_h), pygame.SRCALPHA)
        
        body_color = (25, 25, 30)
        stripe_color = (210, 210, 210)
        silver = (170, 170, 180)
        
        pygame.draw.ellipse(surf, body_color, (0, cyl_h, cyl_w, ellipse_h))
        
        pygame.draw.rect(surf, body_color, (0, ellipse_h // 2, cyl_w, cyl_h))
        
        stripe_w = 4
        stripe_offset = cyl_w - stripe_w - 1
        pygame.draw.rect(surf, stripe_color, (stripe_offset, ellipse_h // 2, stripe_w, cyl_h))
        
        pygame.draw.ellipse(surf, stripe_color, (stripe_offset, cyl_h + 1, stripe_w, ellipse_h - 2))
        
        pygame.draw.ellipse(surf, silver, (0, 0, cyl_w, ellipse_h))
        
        pygame.draw.ellipse(surf, body_color, (0, 0, cyl_w, ellipse_h), 2)
        
        cx, cy = cyl_w // 2, ellipse_h // 2
        pygame.draw.line(surf, (100, 100, 100), (cx - 3, cy), (cx + 3, cy), 1)
        pygame.draw.line(surf, (100, 100, 100), (cx, cy - 2), (cx, cy + 2), 1)
        
        for y_pos in [10, 18, 26]:
            pygame.draw.line(surf, (0, 0, 0), (stripe_offset + 1, y_pos), (stripe_offset + 3, y_pos), 1)
            
        pygame.draw.line(surf, (70, 70, 80), (3, ellipse_h // 2), (3, cyl_h + ellipse_h // 2 - 2), 2)
        
        target_rect = surf.get_rect(midbottom=(mid_x, mid_y + ellipse_h // 2 - 2))
        
        self.screen.blit(surf, target_rect.topleft)

    def draw_custom_inductor(self, component, start_pos, end_pos, mid_x, mid_y, angle, length):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        correct_angle = math.degrees(math.atan2(-dy, dx))
        
        diam = 30
        
        if length > diam:
            scale = (length - diam) / 2 / length
            lead1_end = (start_pos[0] + dx * scale, start_pos[1] + dy * scale)
            lead2_start = (end_pos[0] - dx * scale, end_pos[1] - dy * scale)
            pygame.draw.line(self.screen, (150, 150, 150), start_pos, lead1_end, 2)
            pygame.draw.line(self.screen, (150, 150, 150), lead2_start, end_pos, 2)
            
        surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
        cx, cy = diam // 2, diam // 2
        
        #core ring
        thickness = diam // 3
        outer_r = diam // 2
        
        pygame.draw.circle(surf, (30, 30, 35), (cx, cy), outer_r, width=thickness)
        pygame.draw.circle(surf, (80, 80, 90), (cx, cy), outer_r, width=1) # Outer highlight
        pygame.draw.circle(surf, (15, 15, 20), (cx, cy), outer_r - thickness + 1, width=1) # Inner shadow
        
        #copper wire
        wire_hl = (250, 170, 70)
        wire_base = (200, 120, 30)
        wire_sh = (100, 50, 10)
        num_turns = 18
        
        for i in range(num_turns):
            a = i * (2 * math.pi / num_turns)
            r_in = outer_r - thickness
            r_out = outer_r
            
            x1 = cx + math.cos(a) * (r_in - 1)
            y1 = cy + math.sin(a) * (r_in - 1)
            
            # Midpoint for height
            x2 = cx + math.cos(a + 0.15) * (r_in + (r_out - r_in) * 0.5)
            y2 = cy + math.sin(a + 0.15) * (r_in + (r_out - r_in) * 0.5)

            x3 = cx + math.cos(a + 0.3) * (r_out + 1)
            y3 = cy + math.sin(a + 0.3) * (r_out + 1)
            
            # Shadow/thickness
            pygame.draw.line(surf, wire_sh, (x1, y1), (x3, y3), 4)
            # Main wire color
            pygame.draw.line(surf, wire_base, (x1, y1), (x3, y3), 2)
            # Bright highlight in the center of the wire wrap
            pygame.draw.circle(surf, wire_hl, (int(x2), int(y2)), 1)
            
        rotated_surf = pygame.transform.rotate(surf, correct_angle)
        rect = rotated_surf.get_rect(center=(mid_x, mid_y))
        self.screen.blit(rotated_surf, rect)

    def draw_custom_led(self, component, start_pos, end_pos, mid_x, mid_y, angle, length):
        pygame.draw.line(self.screen, (150, 150, 150), start_pos, (mid_x, mid_y), 2)
        pygame.draw.line(self.screen, (150, 150, 150), end_pos, (mid_x, mid_y), 2)
        
        c_map = {"red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255), 
                 "orange": (255, 165, 0)}
        led_c = c_map.get(getattr(component, 'color', 'red'), (255, 0, 0))
        
        if self.is_simulating or self.sim_paused:
            actual_b = getattr(component, 'brightness', 0)
            b = min(actual_b, 100)
        else:
            actual_b = 0
            b = 0
            
        body_w = 14
        body_h = 16
        
        surf_w = 160
        surf_h = 160
        surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        cx = surf_w // 2
        cy = surf_h - 20
        
        # Base/collar at the bottom
        pygame.draw.rect(surf, (100, 100, 100), (cx - body_w//2 - 2, cy - 4, body_w + 4, 4), border_radius=2)
        pygame.draw.rect(surf, (60, 60, 60), (cx - body_w//2 - 2, cy, body_w + 4, 2), border_radius=1)
        
        body_rect = pygame.Rect(cx - body_w//2, cy - body_h, body_w, body_h)
        base_c = (max(40, int(led_c[0]*0.2)), max(40, int(led_c[1]*0.2)), max(40, int(led_c[2]*0.2)))
        
        if actual_b <= 100.1:
            if b > 0:
                bright_c = (
                    min(255, int(base_c[0] + (led_c[0] * 1.5 - base_c[0]) * (b / 100.0))),
                    min(255, int(base_c[1] + (led_c[1] * 1.5 - base_c[1]) * (b / 100.0))),
                    min(255, int(base_c[2] + (led_c[2] * 1.5 - base_c[2]) * (b / 100.0)))
                )
            else:
                bright_c = base_c
                
            pygame.draw.rect(surf, bright_c, body_rect)
            pygame.draw.circle(surf, bright_c, (cx, cy - body_h), body_w//2)
            
            if b > 0:
                glow_radius_max = int(body_w + (b / 100.0) * 55)
                glow_y = cy - body_h + body_w//4
                glow_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
                
                for r in range(glow_radius_max, body_w//2, -3):
                    ratio = (glow_radius_max - r) / glow_radius_max
                    alpha = int((ratio ** 1.3) * (b / 100.0) * 180)
                    if alpha > 255: alpha = 255
                    
                    whiteness = ratio * 0.4
                    g_c = (
                        min(255, int(led_c[0] + (255 - led_c[0]) * whiteness)),
                        min(255, int(led_c[1] + (255 - led_c[1]) * whiteness)),
                        min(255, int(led_c[2] + (255 - led_c[2]) * whiteness)),
                        alpha
                    )
                    pygame.draw.circle(glow_surf, g_c, (cx, glow_y), r)
                
                surf.blit(glow_surf, (0, 0))
                
                if b >= 95:
                    core_rect = pygame.Rect(cx - body_w//4, cy - body_h//1.5, body_w//2, body_h//2)
                    pygame.draw.rect(surf, (255, 255, 255), core_rect)
                    pygame.draw.circle(surf, (255, 255, 255), (cx, cy - body_h//1.5), body_w//4)

            # Specular highlight
            hl_rect = pygame.Rect(cx - body_w//2 + 3, cy - body_h + 2, body_w//3 - 2, body_h - body_w//2)
            pygame.draw.rect(surf, (255, 255, 255, 120), hl_rect, border_radius=2)
            pygame.draw.circle(surf, (255, 255, 255, 120), (cx - body_w//4, cy - body_h + 2), body_w//4 - 2)

        else:
            char_c = (40, 40, 45)
            pygame.draw.rect(surf, char_c, body_rect)
            pygame.draw.circle(surf, char_c, (cx, cy - body_h), body_w//2)
            pygame.draw.line(surf, (0, 0, 0), (cx - body_w//2, cy - body_h), (cx + body_w//4, cy - body_h//3), 2)
            pygame.draw.line(surf, (0, 0, 0), (cx + body_w//4, cy - body_h//3), (cx - body_w//4, cy - body_h//4), 1)

        target_rect = surf.get_rect(midbottom=(int(mid_x), int(mid_y + 20)))
        self.screen.blit(surf, target_rect.topleft)

    def draw_fallback_component(self, component, x, y, angle, length):
        surf = pygame.Surface((length, 20), pygame.SRCALPHA)
        
        color = (200, 200, 200)
        label = ""
        
        if component.name == "Battery":
            color = (50, 50, 50)
            label = f"{component.voltage}V"
            pygame.draw.rect(surf, color, (0, 0, length, 20), border_radius=4)
            pygame.draw.rect(surf, (200, 200, 200), (4, 4, length-8, 12)) 
            pygame.draw.line(surf, (0,0,0), (length//2 - 5, 10), (length//2 + 5, 10), 2)
            pygame.draw.line(surf, (0,0,0), (length//2, 5), (length//2, 15), 2)

        elif component.name == "Resistor":
            color = (210, 180, 140)
            label = f"{component.resistance}"
            pygame.draw.rect(surf, color, (0, 0, length, 20), border_radius=5)
            pygame.draw.rect(surf, (255, 0, 0), (10, 0, 5, 20))
            pygame.draw.rect(surf, (0, 255, 0), (20, 0, 5, 20))

        elif component.name == "Capacitor":
            color = (200, 200, 200)
            label = f"{format_si(component.capacitance, 'F')}"
            pygame.draw.line(surf, (150, 150, 150), (0, 10), (length//2 - 5, 10), 2)
            pygame.draw.line(surf, (150, 150, 150), (length//2 + 5, 10), (length, 10), 2)
            pygame.draw.line(surf, (0, 0, 0), (length//2 - 5, 2), (length//2 - 5, 18), 3)
            pygame.draw.line(surf, (0, 0, 0), (length//2 + 5, 2), (length//2 + 5, 18), 3)

        elif component.name == "Inductor":
            color = (200, 140, 50)
            label = f"{format_si(component.inductance, 'H')}"
            # Draw coil bumps
            num_bumps = 4
            bump_w = (length - 20) // num_bumps
            for i in range(num_bumps):
                bx = 10 + i * bump_w
                pygame.draw.arc(surf, color, (bx, 2, bump_w, 16), 0, 3.14, 3)

        elif component.name == "LED":
            c_map = {"red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255), 
                     "orange": (255, 165, 0)}
            led_c = c_map.get(getattr(component, 'color', 'red'), (255, 0, 0))
            label = ""
            pygame.draw.ellipse(surf, led_c, (5, 0, length-10, 20))

        # Rotate and blit
        rotated_surf = pygame.transform.rotate(surf, angle)
        rect = rotated_surf.get_rect(center=(x, y))
        self.screen.blit(rotated_surf, rect)
        
        # Draw label near component
        if label:
            text = self.small_font.render(str(label), True, (0, 0, 0))
            self.screen.blit(text, (x - 10, y - 25))
    def create_buttons(self):
        # Component buttons
        self.buttons = []
        componentsList = [Wire, Battery, Resistor, Capacitor, Inductor, LED]
        component_text = ["Wire", "Battery", "Resistor", "Capacitor", "Inductor", "LED"]
        for i, comp in enumerate(component_text):
            btn = Button(50 + i * 110, 30, 100, 45, comp, componentsList[i])
            if comp == self.active_component_txt:
                btn.selected = True
            self.buttons.append(btn)
        self.run_button = Button(730, 30, 80, 45, "Run", None)
        self.help_button_center = (1150, 105)
        self.help_button_radius = 14
        
        self.sim_back_button =  Button(730, 35, 40, 35, "", None, symbol='back10')
        self.sim_pause_button = Button(775, 35, 40, 35, "", None, symbol='pause')
        self.sim_fwd_button =   Button(820, 35, 40, 35, "", None, symbol='fwd10')
        self.sim_reset_button = Button(865, 35, 40, 35, "", None, symbol='reset')
            
        self.sim_time_widget = NumericCounter(1050, 30, 80, 45, label="Time(s)", value=0.0, step=1.0, min_val=0.0, max_val=1e6)
        
        self.clear_button = Button(1110, 650, 70, 30, "Clear", None)
        self.undo_button = Button(1030, 650, 70, 30, "Undo", None)
    
    def open_param_widget_for(self, btn):
        anchor_x = btn.rect.x
        anchor_y = btn.rect.bottom + 6
        self.param_button_rect = btn.rect
        self.param_unit_widget = None        
        if btn.text == "Battery":
            # Create numeric counter for voltage
            default = self.component_defaults.get("Battery", {"val": 9.0, "unit": "V"})
            widget = NumericCounter(anchor_x + 90, anchor_y, 60, 30,
                                    label="Voltage", value=default["val"], step=1, min_val=1e-6, max_val=100000000)
            widget.set_position(anchor_x + 90, anchor_y)
            self.param_widget = widget
            
            unit_opts = ["V", "mV", "kV"]
            self.param_unit_widget = UnitDropdown(anchor_x + 90 + 60 + 40, anchor_y, 50, 30, unit_opts, default["unit"])
            
            self.param_for = "Battery"
        elif btn.text == "Resistor":
            # Create numeric counter for resistance
            default = self.component_defaults.get("Resistor", {"val": 300, "unit": "Ω"})
            widget = NumericCounter(anchor_x + 110, anchor_y, 60, 30,
                                    label="Resistance", value=default["val"], step=100, min_val=1e-3, max_val=1e9)
            widget.set_position(anchor_x + 110, anchor_y)
            self.param_widget = widget
            
            unit_opts = ["Ω", "mΩ", "kΩ", "MΩ"]
            self.param_unit_widget = UnitDropdown(anchor_x + 110 + 60 + 40, anchor_y, 50, 30, unit_opts, default["unit"])
            
            self.param_for = "Resistor"

        elif btn.text == "Capacitor":
            default = self.component_defaults.get("Capacitor", {"val": 10.0, "unit": "µF"})
            widget = NumericCounter(anchor_x + 130, anchor_y, 60, 30,
                                    label="Capacitance", value=default["val"], step=1, min_val=1e-12, max_val=10000)
            widget.set_position(anchor_x + 130, anchor_y)
            self.param_widget = widget
            
            unit_opts = ["F", "mF", "µF", "nF", "pF"]
            self.param_unit_widget = UnitDropdown(anchor_x + 130 + 60 + 40, anchor_y, 50, 30, unit_opts, default["unit"])
            
            self.param_for = "Capacitor"

        elif btn.text == "Inductor":
            default = self.component_defaults.get("Inductor", {"val": 10.0, "unit": "mH"})
            widget = NumericCounter(anchor_x + 120, anchor_y, 60, 30,
                                    label="Inductance", value=default["val"], step=1, min_val=1e-12, max_val=10000)
            widget.set_position(anchor_x + 120, anchor_y)
            self.param_widget = widget
            
            unit_opts = ["H", "mH", "µH", "nH"]
            self.param_unit_widget = UnitDropdown(anchor_x + 120 + 60 + 40, anchor_y, 50, 30, unit_opts, default["unit"])
            
            self.param_for = "Inductor"

        elif btn.text == "LED":
            # Create dropdown for LED color
            default_val = self.component_defaults.get("LED", "red")
            widget = Dropdown(anchor_x + 80, anchor_y, 100, 30,
                              label="Color", options=["red","green","blue","orange"], default=default_val)
            widget.set_position(anchor_x + 80, anchor_y)
            self.param_widget = widget
            self.param_for = "LED"
        else:
            self.param_widget = None
            self.param_for = None
            
        # Ensure active_component gets initialized right away based on the new defaults
        if self.param_widget:
            self.update_active_component_param(self.param_widget.value if not isinstance(self.param_widget, Dropdown) else self.param_widget.selected_option)
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
        # Drop shadow
        pygame.draw.rect(self.screen, (215, 220, 225),
                        (self.board_x + 6, self.board_y + 6, self.board_width, self.board_height),
                        border_radius=10)
        # Main board
        pygame.draw.rect(self.screen, BREADBOARD_COLOR,
                        (self.board_x, self.board_y, self.board_width, self.board_height),
                        border_radius=10)                       
        # border
        pygame.draw.rect(self.screen, (210, 215, 220),
                        (self.board_x, self.board_y, self.board_width, self.board_height),
                        width=2, border_radius=10)
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
        m_pos = self.get_internal_pos(pygame.mouse.get_pos())
        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.screen, self.font, m_pos)
            
        if not self.is_simulating:
            self.run_button.draw(self.screen, self.font, m_pos)
        else:
            self.sim_back_button.draw(self.screen, self.font, m_pos)
            self.sim_pause_button.symbol = 'play' if self.sim_paused else 'pause'
            self.sim_pause_button.draw(self.screen, self.font, m_pos)
            self.sim_fwd_button.draw(self.screen, self.font, m_pos)
            self.sim_reset_button.draw(self.screen, self.font, m_pos)
        if self.sim_time_widget:
            self.sim_time_widget.draw(self.screen, self.font, m_pos)

        # Help button
        hcx, hcy = self.help_button_center
        hr = self.help_button_radius
        hovered = (m_pos[0] - hcx)**2 + (m_pos[1] - hcy)**2 <= hr**2
        help_color = BUTTON_HOVER if hovered else BUTTON_COLOR
        pygame.draw.circle(self.screen, help_color, (hcx, hcy), hr)
        q_surf = self.font.render("?", True, (255, 255, 255))
        self.screen.blit(q_surf, q_surf.get_rect(center=(hcx, hcy)))

        # Draw Side Panel
        if self.side_panel.visible:
            self.side_panel.draw(self.screen)
            
        self.clear_button.draw(self.screen, self.small_font, m_pos)
        self.undo_button.draw(self.screen, self.small_font, m_pos)

    def handle_click(self, pos, button=1):
        def do_select(item):
            if item:
                self.selected_component = item
                for b in self.buttons: b.selected = False
                self.active_component_txt = "Selection"
                if isinstance(item, Wire):
                    item.connected_components = self.get_connected_components(item)
                self.side_panel.set_component(item)
            else:
                self.selected_component = None
                self.side_panel.visible = False

        # Right click for selection
        if button == 3:
            item = self.get_component_at_pos(pos)
            do_select(item)
            return

        if self.param_widget:
            # Check for outside click logic
            bounds = self.param_widget.bounds()
            if self.param_unit_widget:
                bounds.union_ip(self.param_unit_widget.bounds())
                
            clicked_outside = not bounds.collidepoint(pos)

            if self.param_unit_widget:
                unit_val = self.param_unit_widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos))
                if unit_val is not None:
                     self.update_active_component_param(self.param_widget.value)
                     
            val = self.param_widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos))
            if val is not None:
                self.update_active_component_param(val)
                if not clicked_outside:
                    return

            # close if clicked outside
            if clicked_outside:
                if isinstance(self.param_widget, Dropdown):
                    self.param_widget.expanded = False
                if self.param_unit_widget:
                    self.param_unit_widget.expanded = False
                self.param_widget = None
                self.param_unit_widget = None
                self.param_for = None


        if self.clear_button.rect.collidepoint(pos):
            if self.components or self.mergers:
                self.save_state()
            self.components.clear()
            self.mergers.clear()
            for h in self.holes:
                h.occupied = False
            self.first_hole = None
            self.selected_component = None
            self.side_panel.visible = False
            self.side_panel.component = None
            
            if self.is_simulating:
                self.is_simulating = False
                self.sim_time = 0.0
                self.sim_paused = False
                if self.sim_time_widget:
                    self.sim_time_widget.value = 0.0
                    self.sim_time_widget.text = "0.0"
                    
            self.rebuild_circuit()
            return

        if self.undo_button.rect.collidepoint(pos):
            self.undo()
            return

        # Check buttons
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                for b in self.buttons:
                    b.selected = False
                btn.selected = True
                self.active_component_txt = btn.text
                self.selected_component = None # Deselect component when changing tool
                if btn.text == "Wire":
                    self.active_component = Wire(0, 0)
                    self.param_widget = None
                    self.param_for = None
                else:
                    self.open_param_widget_for(btn)
                return

        if not self.is_simulating:
            if self.run_button.rect.collidepoint(pos):
                self.is_simulating = True
                self.sim_paused = False
                print("Started simulation.")
                return
        else:
            if self.sim_reset_button.rect.collidepoint(pos):
                self.is_simulating = False
                self.sim_time = 0.0
                self.sim_paused = False
                if self.sim_time_widget:
                    self.sim_time_widget.value = 0.0
                    self.sim_time_widget.text = "0.0"
                for c in self.components:
                    if isinstance(c, Capacitor):
                        c.voltage_drop = 0.0
                        c._prev_voltage_drop = 0.0
                        c.current = 0.0
                    elif isinstance(c, Inductor):
                        c.voltage_drop = 0.0
                        c.current = 0.0
                        c._prev_current = 0.0
                    elif isinstance(c, Resistor) or isinstance(c, LED):
                        c.voltage_drop = 0.0
                        c.current = 0.0
                    elif isinstance(c, Battery):
                        c.current = 0.0
                print("Stopped simulation.")
                return
            
            if self.sim_pause_button.rect.collidepoint(pos):
                self.sim_paused = not self.sim_paused
                return
                
            if self.sim_back_button.rect.collidepoint(pos):
                new_time = max(0.0, self.sim_time - 10.0)
                self.jump_to_time(new_time)
                return
                
            if self.sim_fwd_button.rect.collidepoint(pos):
                new_time = self.sim_time + 10.0
                self.jump_to_time(new_time)
                return
            
        if self.is_simulating and self.sim_time_widget:
            if self.sim_time_widget.bounds().collidepoint(pos):
                return

        hcx, hcy = self.help_button_center
        if (pos[0] - hcx)**2 + (pos[1] - hcy)**2 <= self.help_button_radius**2:
            self.tutorial_manager.start_tutorial()
            return

        # Check holes for placement
        for hole in self.holes:
            if hole.contains(pos):
                # Cannot use occupied holes
                if hole.occupied:
                    return

                if self.first_hole is None:
                    self.first_hole = hole
                    self.active_component.node_id_1 = hole.node_id
                    print(f"Start: row={hole.row}, col={hole.col}, rail={hole.is_rail} [Node {hole.node_id}]")
                else:
                    if hole == self.first_hole:
                        return
                        
                    self.save_state()
                    
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
                    elif isinstance(self.active_component, Capacitor):
                        self.active_component = Capacitor(0, 0, None, None, self.active_component.capacitance, 0.0)
                    elif isinstance(self.active_component, Inductor):
                        self.active_component = Inductor(0, 0, None, None, self.active_component.inductance, 0.0)
                    elif isinstance(self.active_component, LED):
                        self.active_component = LED(0, 0, None, None, 220, 0.0, self.active_component.color)
                        
                    # Mark holes as occupied
                    self.first_hole.occupied = True
                    hole.occupied = True
                    
                    self.first_hole = None
                return 

    def update_active_component_param(self, value):
        multiplier = 1.0
        u = ""
        if self.param_unit_widget:
             u = self.param_unit_widget.selected_option
             if u in ["kV", "kΩ"]: multiplier = 1e3
             elif u in ["MΩ"]: multiplier = 1e6
             elif u in ["mV", "mΩ", "mF", "mH"]: multiplier = 1e-3
             elif u in ["µF", "µH"]: multiplier = 1e-6
             elif u in ["nF", "nH"]: multiplier = 1e-9
             elif u in ["pF"]: multiplier = 1e-12
        if self.active_component_txt == "LED":
            actual_val = value # For LEDs, value is the color string
        else:
            actual_val = value * multiplier
        
        if self.active_component_txt == "Battery":
             self.active_component = Battery(0, 0, None, None, actual_val)
             self.component_defaults["Battery"] = {"val": value, "unit": u}
        elif self.active_component_txt == "Resistor":
             self.active_component = Resistor(0, 0, None, None, actual_val, 0.0)
             self.component_defaults["Resistor"] = {"val": value, "unit": u}
        elif self.active_component_txt == "Capacitor":
             self.active_component = Capacitor(0, 0, None, None, actual_val, 0.0)
             self.component_defaults["Capacitor"] = {"val": value, "unit": u}
        elif self.active_component_txt == "Inductor":
             self.active_component = Inductor(0, 0, None, None, actual_val, 0.0)
             self.component_defaults["Inductor"] = {"val": value, "unit": u}
        elif self.active_component_txt == "LED":
             self.active_component = LED(0, 0, None, None, 220, 0.0, value)
             self.component_defaults["LED"] = value

    def jump_to_time(self, target_time):
        self.sim_paused = True
        self.sim_time = target_time
        if self.sim_time_widget:
            self.sim_time_widget.value = target_time
        
        # Reset back to 0
        for c in self.components:
            if isinstance(c, Capacitor):
                c.voltage_drop = 0.0
                c._prev_voltage_drop = 0.0
                c.current = 0.0
            elif isinstance(c, Inductor):
                c.voltage_drop = 0.0
                c.current = 0.0
                c._prev_current = 0.0
            elif isinstance(c, Resistor) or isinstance(c, LED):
                c.voltage_drop = 0.0
                c.current = 0.0
            elif isinstance(c, Battery):
                c.current = 0.0
                
        if len(self.components) == 0:
            return
            
        active_nodes = list(set([c.node_id_1 for c in self.components] + [c.node_id_2 for c in self.components]))
        tau = calculate_time_constant(self.components)
        if tau is None or tau < 1e-6:
            total_R = sum(c.resistance for c in self.components if isinstance(c, Resistor))
            total_C = sum(c.capacitance for c in self.components if isinstance(c, Capacitor))
            total_L = sum(c.inductance for c in self.components if isinstance(c, Inductor))
            if total_R > 0 and total_C > 0:
                tau = total_R * total_C
            elif total_R > 0 and total_L > 0:
                tau = total_L / total_R
            elif total_L > 0 and total_C > 0:
                import math
                tau = 2 * math.pi * math.sqrt(total_L * total_C)
        self.current_tau = tau
        dt_base = tau / 60.0 if tau else 1/60.0
        self.current_dt = dt_base
        
        dt_sim = dt_base / 100.0 if dt_base > 0 else 1/6000.0
        steps = int(target_time / dt_sim) if dt_sim > 0 else 0
        
        MAX_STEPS = 10000
        if steps > MAX_STEPS:
            dt_sim = target_time / MAX_STEPS
            steps = MAX_STEPS
            
        remainder = target_time - (steps * dt_sim)
        
        matrix = generate_incidence_matrix(self.components, active_nodes)
        
        # Simulate forward
        for _ in range(steps):
             ModifiedNodalAnalysis(matrix, self.components, active_nodes, dt=dt_sim)
             
        # Simulate exact remainder
        if remainder > 1e-6:
             ModifiedNodalAnalysis(matrix, self.components, active_nodes, dt=remainder)

    def get_internal_pos(self, pos):
        win_w, win_h = self.window.get_size()
        scale = min(win_w / WINDOW_WIDTH, win_h / WINDOW_HEIGHT)
        scaled_w = int(WINDOW_WIDTH * scale)
        scaled_h = int(WINDOW_HEIGHT * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2
        # Subtract letterbox offset then un-scale
        x = int((pos[0] - offset_x) / scale)
        y = int((pos[1] - offset_y) / scale)
        # Clamp to internal surface bounds
        x = max(0, min(WINDOW_WIDTH - 1, x))
        y = max(0, min(WINDOW_HEIGHT - 1, y))
        return (x, y)


    async def run(self):
        # Main loop
        running = True
        while running:
            # Poll browser window size every frame and resize if needed
            if sys.platform == "emscripten":
                import platform as _platform
                w = int(_platform.window.innerWidth)
                h = int(_platform.window.innerHeight)
                if (w, h) != self.window.get_size():
                    self.window = pygame.display.set_mode((w, h))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.VIDEORESIZE and sys.platform != "emscripten":
                    self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    continue

                if hasattr(event, 'pos'):
                    evt_dict = event.dict.copy()
                    evt_dict['pos'] = self.get_internal_pos(event.pos)
                    event = pygame.event.Event(event.type, evt_dict)

                if self.tutorial_manager.active:
                    if self.tutorial_manager.handle_event(event):
                        continue

                handled_by_time_widget = False
                if self.sim_time_widget:
                    val = self.sim_time_widget.handle_event(event)
                    if val is not None:
                        if not self.is_simulating:
                            self.is_simulating = True
                        self.jump_to_time(val)
                        handled_by_time_widget = True
                    if event.type == pygame.MOUSEBUTTONDOWN and hasattr(self.sim_time_widget, 'bounds') and self.sim_time_widget.bounds().collidepoint(event.pos):
                        handled_by_time_widget = True
                    elif event.type == pygame.KEYDOWN and hasattr(self.sim_time_widget, 'active') and self.sim_time_widget.active:
                        handled_by_time_widget = True
                        
                if handled_by_time_widget:
                    continue
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos, event.button)
                elif event.type == pygame.KEYDOWN:
                    widget_handled_key = False
                    if self.param_widget:
                        value = self.param_widget.handle_event(event)
                        if value is not None:
                            self.update_active_component_param(value)
                        if hasattr(self.param_widget, 'active') and self.param_widget.active:
                            widget_handled_key = True
                            
                    if not widget_handled_key and (event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE):
                        self.delete_selected_component()
                elif event.type == pygame.MOUSEMOTION:
                    self.hovered_hole = None
                    for hole in self.holes:
                        if hole.contains(event.pos):
                            self.hovered_hole = hole
                            break
                    
            # Update tutorial
            self.tutorial_manager.update()

            if self.is_simulating:
                if self.sim_time_widget:
                    self.sim_time_widget.value = self.sim_time
                if not self.sim_paused and len(self.components) > 0:
                    active_nodes = list(set([c.node_id_1 for c in self.components] + [c.node_id_2 for c in self.components]))
                    try:
                        matrix = generate_incidence_matrix(self.components, active_nodes)
                        tau = calculate_time_constant(self.components)
                        if tau is None or tau < 1e-6:
                            total_R = sum(c.resistance for c in self.components if isinstance(c, Resistor))
                            total_C = sum(c.capacitance for c in self.components if isinstance(c, Capacitor))
                            total_L = sum(c.inductance for c in self.components if isinstance(c, Inductor))
                            if total_R > 0 and total_C > 0:
                                tau = total_R * total_C
                            elif total_R > 0 and total_L > 0:
                                tau = total_L / total_R
                            elif total_L > 0 and total_C > 0:
                                import math
                                tau = 2 * math.pi * math.sqrt(total_L * total_C)
                        self.current_tau = tau
                        dt_base = tau / 60.0 if tau else 1/60.0
                        self.current_dt = dt_base
                        
                        substeps = 10
                        dt_sim = dt_base / substeps
                        for _ in range(substeps):
                            ModifiedNodalAnalysis(matrix, self.components, active_nodes, dt=dt_sim)
                            
                        self.sim_time += dt_base
                    except Exception as e:
                        print(f"Simulation warning: {e}")
            
            self.screen.fill(BG_COLOR)
            
            # Draw UI            
            self.draw_breadboard()
            m_pos = self.get_internal_pos(pygame.mouse.get_pos())
            if self.param_widget:
                self.param_widget.draw(self.screen, self.font, m_pos)
            if self.param_unit_widget:
                self.param_unit_widget.draw(self.screen, self.font, m_pos)

            # Draw tutorial overlay
            self.tutorial_manager.draw(self.screen)

            # Scale and blit to window
                        # Scale with aspect ratio preserved, letterboxing if needed
            win_w, win_h = self.window.get_size()
            scale = min(win_w / WINDOW_WIDTH, win_h / WINDOW_HEIGHT)
            scaled_w = int(WINDOW_WIDTH * scale)
            scaled_h = int(WINDOW_HEIGHT * scale)
            offset_x = (win_w - scaled_w) // 2
            offset_y = (win_h - scaled_h) // 2
            scaled = pygame.transform.smoothscale(self.screen, (scaled_w, scaled_h))
            self.window.fill(BG_COLOR)
            self.window.blit(scaled, (offset_x, offset_y))

            # Copyright notice — drawn on window so it anchors to the real corner
            copyright_surf = self.copyright_font.render("\u00a9 2026 Anay Gokhale | Licensed under Apache 2.0", True, (160, 170, 180))
            self.window.blit(copyright_surf, (5, win_h - copyright_surf.get_height() - 5))
            pygame.display.flip()
            self.clock.tick(60)
            await asyncio.sleep(0)
        
        pygame.quit()

# Run the simulator
if __name__ == "__main__":
    app = BreadboardSimulator()
    asyncio.run(app.run())
