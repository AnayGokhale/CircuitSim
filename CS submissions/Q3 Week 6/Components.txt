'''
Included components: Wire, Battery, Resistor, LED
'''
class Wire:
    def __init__(self, node1, node2, name="Wire"):
        self.node1 = node1
        self.node2 = node2
        self.name = name
        self.connected_components = []
class Battery:
    def __init__(self, node1, node2, node_id_1, node_id_2, voltage, name="Battery"):
        self.node1 = node1
        self.node2 = node2
        self.node_id_1 = node_id_1
        self.node_id_2 = node_id_2
        self.voltage = voltage
        self.name = name
        self.current = 0.0
class Resistor:
    def __init__(self, node1, node2, node_id_1, node_id_2, resistance, voltage_drop, name="Resistor"):
        self.node1 = node1
        self.node2 = node2
        self.node_id_1 = node_id_1
        self.node_id_2 = node_id_2
        self.resistance = resistance
        self.voltage_drop = voltage_drop
        self.name = name
        self.current = 0.0
    
    def get_color_bands(self, resistance):    
        colors = ["black", "brown", "red", "orange", "yellow", "green", "blue", "violet", "gray", "white"]
        if resistance <= 0:
            return ["black", "black", "black", "gold"]
            
        s_val = f"{resistance:.2e}"
        base, exponent = s_val.split('e')
        base_val = float(base)
        exponent = int(exponent)
        
        r_val = int(resistance)
        s = str(r_val)
        if len(s) < 2:
            d1 = int(s[0])
            d2 = 0
            mult = 0
            return [colors[d1], "black", "gold", "gold"]
            
        d1 = int(s[0])
        d2 = int(s[1])
        
        zeros = len(s) - 2
        
        if zeros < 0: zeros = 0
        if zeros > 9: zeros = 9
        
        return [colors[d1], colors[d2], colors[zeros], "gold"]
class LED:
    def __init__(self, node1, node2, node_id_1, node_id_2, resistance, voltage_drop, color, name="LED"):
        self.node1 = node1
        self.node2 = node2
        self.node_id_1 = node_id_1
        self.node_id_2 = node_id_2
        self.resistance = resistance
        self.voltage_drop = voltage_drop
        self.color = color
        self.name = name
        self.current = 0
        self.brightness = 0.0