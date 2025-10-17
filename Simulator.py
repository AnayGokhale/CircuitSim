import tkinter as tk

# --- Configuration Constants ---
BREADBOARD_WIDTH = 600
BREADBOARD_HEIGHT = 400
BREADBOARD_COLOR = "#C0C0C0" # A nice grey for the plastic
HOLE_SIZE = 4
HOLE_COLOR = "#000000"
HOLE_SPACING = 10

class BreadboardSimulatorApp:
    """
    The main application class for the breadboard simulator GUI.
    """
    def __init__(self, master):
        self.master = master
        master.title("Python Breadboard Simulator")

        # Create the canvas where the breadboard and components will be drawn
        self.canvas = tk.Canvas(
            master, 
            width=BREADBOARD_WIDTH + 100, # Extra space for controls/measurements
            height=BREADBOARD_HEIGHT + 100, 
            bg="#FFFFFF" # White background for the whole area
        )
        self.canvas.pack(padx=20, pady=20)
        
        # Draw the breadboard outline
        self.draw_breadboard_base(50, 50)
        
        # Placeholder for controls/measurements
        self.draw_info_panel()

    def draw_breadboard_base(self, start_x, start_y):
        """
        Draws the grey base and the array of holes (nodes) on the breadboard.
        """
        # Draw the main plastic block
        self.canvas.create_rectangle(
            start_x, start_y, 
            start_x + BREADBOARD_WIDTH, start_y + BREADBOARD_HEIGHT,
            fill=BREADBOARD_COLOR, 
            outline=HOLE_COLOR
        )
        
        # --- Draw Holes (The 'Nodes' of the circuit) ---
        
        # Simple example: a 10x10 grid of holes to represent nodes
        self.node_locations = []
        rows = 10
        cols = 50 
        
        # Center Channel (The 'Valley' in the middle of a breadboard)
        center_channel_offset = 30 # Space for the valley

        # The 'A-E' and 'F-J' sections
        for section in range(2): 
            y_offset = start_y + (BREADBOARD_HEIGHT // 2) * section + (center_channel_offset // 2) * section
            
            for row in range(rows):
                for col in range(cols):
                    # Calculate the center of the hole
                    x = start_x + (col * HOLE_SPACING) + 15
                    y = y_offset + (row * HOLE_SPACING) + 15
                    
                    # Offset for the second section (F-J)
                    if section == 1:
                        y += center_channel_offset 

                    # Draw the hole (a small black circle)
                    self.canvas.create_oval(
                        x - HOLE_SIZE // 2, y - HOLE_SIZE // 2,
                        x + HOLE_SIZE // 2, y + HOLE_SIZE // 2,
                        fill=HOLE_COLOR, 
                        outline=""
                    )
                    # Store location for component placement logic later
                    self.node_locations.append((x, y))
                    
        print(f"Total nodes drawn: {len(self.node_locations)}")
        
    def draw_info_panel(self):
        """
        Draws a simple panel for displaying measurements or controls.
        """
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
    # 1. Create the main Tkinter window
    root = tk.Tk()
    
    # 2. Instantiate the application
    app = BreadboardSimulatorApp(root)
    
    # 3. Start the Tkinter event loop
    # This keeps the window open and responsive to user input
    root.mainloop()