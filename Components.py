'''
Included components: Wire, Battery, Resistor, LED
'''
class Wire:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2

class Battery:
    def __init__(self, node1, node2, voltage):
        self.node1 = node1
        self.node2 = node2
        self.voltage = voltage

class Resistor:
    def __init__(self, node1, node2, resistance):
        self.node1 = node1
        self.node2 = node2
        self.resistance = resistance

class LED:
    def __init__(self, node1, node2, resistance, color):
        self.node1 = node1
        self.node2 = node2
        self.resistance = resistance
        self.color = color