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