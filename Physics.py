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
    G = np.zeros((len(loads), len(loads)))
    for i in range(len(loads)):
        for j in range(len(loads)):
            if i == j:
                G[i][j] = 1/loads[i].resistance
    Master = np.block([
        [load_matrix.T@G@load_matrix, source_matrix.T],
        [source_matrix, np.atleast_2d(np.zeros((len(source_matrix), len(source_matrix))))]
    ])
    Z = np.zeros(len(active_nodes) + len(sources))
    for i, source in enumerate(sources):
        Z[i + len(active_nodes)] = source.voltage
    gnd_idx = active_nodes.index(0)
    M_reduced = np.delete(Master, gnd_idx, axis=0)
    M_reduced = np.delete(M_reduced, gnd_idx, axis=1)
    Z_reduced = np.delete(Z, gnd_idx)
    x = np.linalg.solve(M_reduced, Z_reduced)
    voltages_reduced = x[:len(active_nodes)-1]
    # Re-insert the 0.0V at the correct gnd_idx to align with active_nodes
    full_voltages = np.insert(voltages_reduced, gnd_idx, 0.0)
    
    battery_currents = x[len(active_nodes)-1:]
    return full_voltages, battery_currents
    

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