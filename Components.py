'''
Included components: Wire, Battery, Resistor, LED
'''
class Wire:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2

class Battery:
    def __init__(self, positive_node, negative_node, voltage):
        self.positive_node = positive_node
        self.negative_node = negative_node
        self.voltage = voltage

class Resistor:
    def __init__(self, node1, node2, resistance):
        self.node1 = node1
        self.node2 = node2
        self.resistance = resistance

class LED:
    def __init__(self, anode_node, cathode_node, resistance, forward_voltage):
        self.anode_node = anode_node
        self.cathode_node = cathode_node
        self.resistance = resistance
        self.forward_voltage = forward_voltage

