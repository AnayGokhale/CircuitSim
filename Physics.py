from Components import Wire, Battery, Resistor, LED
import numpy as np
from scipy.linalg import null_space

def ModifiedNodalAnalysis(incidence_matrix, components, active_nodes):
    loads = [component for component in components if component.name != "Battery"]
    sources = [component for component in components if component.name == "Battery"]
    load_matrix = [row for i, row in enumerate(incidence_matrix) if components[i].name != "Battery"]
    source_matrix = [row for i, row in enumerate(incidence_matrix) if components[i].name == "Battery"]
    load_matrix = np.atleast_2d(load_matrix)
    source_matrix = np.atleast_2d(source_matrix)

    # Create Conductance Matrix
    G = np.zeros((len(loads), len(loads)))
    for i in range(len(loads)):
        for j in range(len(loads)):
            if i == j:
                G[i][j] = 1/loads[i].resistance
    
    # Create Master Matrix
    Master = np.block([
        [load_matrix.T@G@load_matrix, source_matrix.T],
        [source_matrix, np.atleast_2d(np.zeros((len(source_matrix), len(source_matrix))))]
    ])

    # Create Z Vector
    Z = np.zeros(len(active_nodes) + len(sources))
    for i, source in enumerate(sources):
        Z[i + len(active_nodes)] = source.voltage
    gnd_idx = active_nodes.index(0)

    # Remove Ground Row and Column
    M_reduced = np.delete(Master, gnd_idx, axis=0)
    M_reduced = np.delete(M_reduced, gnd_idx, axis=1)
    Z_reduced = np.delete(Z, gnd_idx)

    # Solve for Voltages
    x = np.linalg.solve(M_reduced, Z_reduced)
    voltages_reduced = x[:len(active_nodes)-1]
    full_voltages = np.insert(voltages_reduced, gnd_idx, 0.0)
    battery_currents = x[len(active_nodes)-1:]
    
    # Calculate voltage drops and currents
    voltage_dict = {}
    for i, voltage in enumerate(full_voltages):
        voltage_dict[active_nodes[i]] = voltage

    for i, source in enumerate(sources):
        source.current = float(battery_currents[i])

    for component in components:
        if isinstance(component, Resistor) or isinstance(component, LED):
            v1 = voltage_dict.get(component.node_id_1, 0)
            v2 = voltage_dict.get(component.node_id_2, 0)
            component.voltage_drop = abs(v1 - v2)
            if component.resistance > 0:
                component.current = component.voltage_drop / component.resistance
            else:
                component.current = 0
            
            if isinstance(component, LED):
                component.brightness = calculate_brightness(component)
    
    return full_voltages, battery_currents

def calculate_brightness(led_component):
    MAX_POWER = 0.040 
    
    if led_component.current <= 0:
        return 0.0
        
    power = led_component.current * led_component.voltage_drop
    
    # Brightness as percentage of max power
    percentage = (power / MAX_POWER) * 100
    
    return max(0.0, min(100.0, percentage))

def generate_incidence_matrix(components, active_nodes):
    incidence_matrix = np.zeros((len(components), len(active_nodes)))
    for i, component in enumerate(components):
        for j, node in enumerate(active_nodes):
            if component.node_id_1 == node:
                incidence_matrix[i][j] = -1
            elif component.node_id_2 == node:
                incidence_matrix[i][j] = 1
    return incidence_matrix

def calculate_resistance_in_series(resistances):
    return sum(resistances)

def calculate_resistance_in_parallel(resistances):
    if not resistances:
        return 0
    inverse_sum = sum(1/r for r in resistances if r != 0)
    if inverse_sum == 0:
        return float('inf')
    return 1 / inverse_sum