from Components import Wire, Battery, Resistor, LED

def create_physical_component(component_type, *args, **kwargs):
    if component_type == "Wire":
        return Wire(*args, **kwargs)
    elif component_type == "Battery":
        return Battery(*args, **kwargs)
    elif component_type == "Resistor":
        return Resistor(*args, **kwargs)
    elif component_type == "LED":
        return LED(*args, **kwargs)
    else:
        raise ValueError(f"Unknown component type: {component_type}")
    
def path_matrix(components):
    incidence_matrix = []
    for n in range(len(components)):
        incidence_matrix.append([0] * len(components))
    start_nodes = [component.node1 for component in components]
    end_nodes = [component.node2 for component in components]
    for endNode in end_nodes:
        for startNode in start_nodes:
            if endNode == startNode:
                raise ValueError("Cannot create a path between the same node")
            if endNode is None or startNode is None:
                raise ValueError("Node cannot be None")
            if endNode[0] == "vertical" and startNode[0] == "vertical":
                c1 = end_nodes.index(endNode)
                c2 = start_nodes.index(startNode)
                incidence_matrix[c1][c1] = -1
                incidence_matrix[c1][c2] = 1
            elif endNode[0] == "horizontal" and startNode[0] == "horizontal":
                c1 = end_nodes.index(endNode)
                c2 = start_nodes.index(startNode)
                incidence_matrix[c1][c1] = -1
                incidence_matrix[c1][c2] = 1

def calculate_resistance_in_series(resistances):
    return sum(resistances)

def calculate_resistance_in_parallel(resistances):
    if not resistances:
        return 0
    inverse_sum = sum(1/r for r in resistances if r != 0)
    if inverse_sum == 0:
        return float('inf')
    return 1 / inverse_sum
