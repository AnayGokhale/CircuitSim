from Components import Wire, Battery, Resistor, LED
import numpy as np
from scipy.linalg import null_space

def ModifiedNodalAnalysis(incidence_matrix, components, active_nodes):
    loads = [component for component in components if component.name != "Battery"]
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
    return Master
    

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