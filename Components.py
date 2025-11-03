'''
Included components: Wire, Battery, Resistor, LED
'''
class Wire:
    def __init__(self, node1, node2, name="Wire"):
        self.node1 = node1
        self.node2 = node2
        self.name = name
class Battery:
    def __init__(self, node1, node2, voltage, name="Battery"):
        self.node1 = node1
        self.node2 = node2
        self.voltage = voltage
        self.name = name
class Resistor:
    def __init__(self, node1, node2, resistance, name="Resistor"):
        self.node1 = node1
        self.node2 = node2
        self.resistance = resistance
        self.name = name
class LED:
    def __init__(self, node1, node2, resistance, color, name="LED"):
        self.node1 = node1
        self.node2 = node2
        self.resistance = resistance
        self.color = color
        self.name = name