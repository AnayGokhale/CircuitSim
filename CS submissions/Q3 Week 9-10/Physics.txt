from Components import Wire, Battery, Resistor, Capacitor, LED
import numpy as np
from scipy.linalg import null_space

def ModifiedNodalAnalysis(incidence_matrix, components, active_nodes, dt=1/60.0):
    loads = [component for component in components if component.name != "Battery"]
    sources = [component for component in components if component.name == "Battery"]
    load_matrix = [row for i, row in enumerate(incidence_matrix) if components[i].name != "Battery"]
    source_matrix = [row for i, row in enumerate(incidence_matrix) if components[i].name == "Battery"]
    load_matrix = np.atleast_2d(load_matrix)
    source_matrix = np.atleast_2d(source_matrix)

    # Conductance Matrix
    G = np.zeros((len(loads), len(loads)))
    for i in range(len(loads)):
        for j in range(len(loads)):
            if i == j:
                if loads[i].name == "Capacitor":
                    G[i][j] = loads[i].capacitance / dt
                else:
                    if loads[i].resistance > 0:
                        G[i][j] = 1 / loads[i].resistance
                    else:
                        G[i][j] = 1e9  # Very high conductance for 0 resistance to avoid singular matrices
    
    # Master Matrix
    Master = np.block([
        [load_matrix.T@G@load_matrix, source_matrix.T],
        [source_matrix, np.atleast_2d(np.zeros((len(source_matrix), len(source_matrix))))]
    ])

    # Infintely small conductance to avoid singular matrices
    GMIN = 1e-12
    for i in range(len(active_nodes)):
        Master[i][i] += GMIN

    # Z Vector
    Z = np.zeros(len(active_nodes) + len(sources))
    
    # Add historical current from capacitors
    for i, component in enumerate(components):
        if component.name == "Capacitor":
            # Companion model: Ieq = (C / dt) * V_prev
            # _prev_voltage_drop stores signed (v1 - v2), matching v_drop convention
            # Incidence matrix has v_branch = v2 - v1 = -v_drop, so signs must flip
            Ieq = (component.capacitance / dt) * component._prev_voltage_drop
            if component.node_id_1 in active_nodes:
                idx1 = active_nodes.index(component.node_id_1)
                Z[idx1] += Ieq
            if component.node_id_2 in active_nodes:
                idx2 = active_nodes.index(component.node_id_2)
                Z[idx2] -= Ieq

    for i, source in enumerate(sources):
        Z[i + len(active_nodes)] = source.voltage
        
    if 0 in active_nodes:
        gnd_idx = active_nodes.index(0)
    else:
        gnd_idx = 0

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
        if isinstance(component, Resistor) or isinstance(component, LED) or isinstance(component, Capacitor):
            v1 = voltage_dict.get(component.node_id_1, 0)
            v2 = voltage_dict.get(component.node_id_2, 0)
            
            # Voltage drop from node1 to node2
            v_drop = v1 - v2
            
            if isinstance(component, Capacitor):
                V_old = component._prev_voltage_drop
                G_eq = component.capacitance / dt
                component.current = G_eq * (v_drop - V_old)
                component.voltage_drop = abs(v_drop)
                component._prev_voltage_drop = v_drop
            else:
                component.voltage_drop = abs(v_drop)
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

def calculate_time_constant(components):
    resistive = [c for c in components if isinstance(c, (Resistor, LED))]
    capacitors = [c for c in components if isinstance(c, Capacitor)]
    batteries = [c for c in components if isinstance(c, Battery)]
    
    if not resistive or not capacitors:
        return None
    
    all_nodes = list(set(
        [c.node_id_1 for c in components if not isinstance(c, Wire)] +
        [c.node_id_2 for c in components if not isinstance(c, Wire)]
    ))
    
    n = len(all_nodes)
    if n < 2:
        return None
    
    Y = np.zeros((n, n))
    for r in resistive:
        if r.resistance > 0:
            g = 1.0 / r.resistance
            i = all_nodes.index(r.node_id_1)
            j = all_nodes.index(r.node_id_2)
            Y[i][i] += g
            Y[j][j] += g
            Y[i][j] -= g
            Y[j][i] -= g
    
    for bat in batteries:
        g = 1e9 
        i = all_nodes.index(bat.node_id_1)
        j = all_nodes.index(bat.node_id_2)
        Y[i][i] += g
        Y[j][j] += g
        Y[i][j] -= g
        Y[j][i] -= g
    
    for i in range(n):
        Y[i][i] += 1e-12
    
    taus = []
    for cap in capacitors:
        ci = all_nodes.index(cap.node_id_1)
        cj = all_nodes.index(cap.node_id_2)
        if ci == cj:
            continue
        
        I_vec = np.zeros(n)
        I_vec[ci] = 1.0
        I_vec[cj] = -1.0
        
        ref = 0
        Y_red = np.delete(np.delete(Y, ref, axis=0), ref, axis=1)
        I_red = np.delete(I_vec, ref)
        
        try:
            V_red = np.linalg.solve(Y_red, I_red)
            V_full = np.insert(V_red, ref, 0.0)
            R_th = abs(V_full[ci] - V_full[cj])
            tau = R_th * cap.capacitance
            if tau > 0:
                taus.append(tau)
        except np.linalg.LinAlgError:
            pass
    
    return max(taus) if taus else None