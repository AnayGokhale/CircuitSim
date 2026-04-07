from Components import Wire, Battery, Resistor, Capacitor, Inductor, LED
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
                elif loads[i].name == "Inductor":
                    if loads[i].inductance > 0:
                        G[i][j] = dt / loads[i].inductance
                    else:
                        G[i][j] = 1e9
                else:
                    if loads[i].resistance > 0:
                        G[i][j] = 1 / loads[i].resistance
                    else:
                        G[i][j] = 1e9  # Very high conductance for 0 resistance to avoid singular matrices
    
    # Infintely small conductance to avoid singular matrices
    GMIN = 1e-12
    # Z Vector
    Z = np.zeros(len(active_nodes) + len(sources))
        
    if len(sources) == 0:
        # Battery-less circuit Support (RC Discharge)
        Master = load_matrix.T @ G @ load_matrix
        for i in range(len(active_nodes)):
            Master[i][i] += GMIN
            
        # Add historical current from capacitors and inductors
        for i, component in enumerate(components):
            if component.name == "Capacitor":
                Ieq = (component.capacitance / dt) * component._prev_voltage_drop
                if component.node_id_1 in active_nodes:
                    idx1 = active_nodes.index(component.node_id_1)
                    Z[idx1] += Ieq
                if component.node_id_2 in active_nodes:
                    idx2 = active_nodes.index(component.node_id_2)
                    Z[idx2] -= Ieq
            elif component.name == "Inductor":
                Ieq = component._prev_current
                if component.node_id_1 in active_nodes:
                    idx1 = active_nodes.index(component.node_id_1)
                    Z[idx1] -= Ieq
                if component.node_id_2 in active_nodes:
                    idx2 = active_nodes.index(component.node_id_2)
                    Z[idx2] += Ieq
        
        gnd_idx = active_nodes.index(0) if 0 in active_nodes else 0
        
        M_reduced = np.delete(Master, gnd_idx, axis=0)
        M_reduced = np.delete(M_reduced, gnd_idx, axis=1)
        Z_reduced = np.delete(Z[:len(active_nodes)], gnd_idx)
        
        try:
            voltages_reduced = np.linalg.solve(M_reduced, Z_reduced)
        except np.linalg.LinAlgError:
            voltages_reduced = np.zeros(len(active_nodes) - 1)
            
        full_voltages = np.insert(voltages_reduced, gnd_idx, 0.0)
        battery_currents = []
        
    else:
        # Standard block matrix with Battery sources
        Master = np.block([
            [load_matrix.T@G@load_matrix, source_matrix.T],
            [source_matrix, np.atleast_2d(np.zeros((len(source_matrix), len(source_matrix))))]
        ])
        
        for i in range(len(active_nodes)):
            Master[i][i] += GMIN

        # Add historical current from capacitors and inductors
        for i, component in enumerate(components):
            if component.name == "Capacitor":
                Ieq = (component.capacitance / dt) * component._prev_voltage_drop
                if component.node_id_1 in active_nodes:
                    idx1 = active_nodes.index(component.node_id_1)
                    Z[idx1] += Ieq
                if component.node_id_2 in active_nodes:
                    idx2 = active_nodes.index(component.node_id_2)
                    Z[idx2] -= Ieq
            elif component.name == "Inductor":
                Ieq = component._prev_current
                if component.node_id_1 in active_nodes:
                    idx1 = active_nodes.index(component.node_id_1)
                    Z[idx1] -= Ieq
                if component.node_id_2 in active_nodes:
                    idx2 = active_nodes.index(component.node_id_2)
                    Z[idx2] += Ieq

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
        try:
            x = np.linalg.solve(M_reduced, Z_reduced)
        except np.linalg.LinAlgError:
            x = np.zeros(len(M_reduced))
            
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
        if isinstance(component, (Resistor, LED, Capacitor, Inductor)):
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
            elif isinstance(component, Inductor):
                G_eq = dt / component.inductance if component.inductance > 0 else 1e9
                component.current = G_eq * v_drop + component._prev_current
                component.voltage_drop = abs(v_drop)
                component._prev_current = component.current
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
    inductors = [c for c in components if isinstance(c, Inductor)]
    batteries = [c for c in components if isinstance(c, Battery)]
    
    has_rc = resistive and capacitors
    has_rl = resistive and inductors
    has_lc = inductors and capacitors
    
    if not has_rc and not has_rl and not has_lc:
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
        
    taus = []



    # Group parallel capacitors by their node pair
    cap_groups = {}
    for cap in capacitors:
        key = (min(cap.node_id_1, cap.node_id_2), max(cap.node_id_1, cap.node_id_2))
        if key not in cap_groups:
            cap_groups[key] = []
        cap_groups[key].append(cap)

    #For each capacitor GROUP, compute tau with all other groups OPEN
    for group_key, group_caps in cap_groups.items():
        ci = all_nodes.index(group_key[0])
        cj = all_nodes.index(group_key[1])
        if ci == cj:
            continue

        C_total = sum(c.capacitance for c in group_caps)

        Y_cap = np.copy(Y)
        for i in range(n):
            Y_cap[i][i] += 1e-12

        I_vec = np.zeros(n)
        I_vec[ci] = 1.0
        I_vec[cj] = -1.0

        ref = 0
        Y_red = np.delete(np.delete(Y_cap, ref, axis=0), ref, axis=1)
        I_red = np.delete(I_vec, ref)

        try:
            V_red = np.linalg.solve(Y_red, I_red)
            V_full = np.insert(V_red, ref, 0.0)
            R_th = abs(V_full[ci] - V_full[cj])
            tau = R_th * C_total
            if tau > 1e-9 and tau < 1e5:
                taus.append(tau)
        except np.linalg.LinAlgError:
            pass

    #For each capacitor GROUP, compute tau with all other groups SHORTED
    group_keys = list(cap_groups.keys())
    for gidx, group_key in enumerate(group_keys):
        ci = all_nodes.index(group_key[0])
        cj = all_nodes.index(group_key[1])
        if ci == cj:
            continue

        C_total = sum(c.capacitance for c in cap_groups[group_key])

        Y_cap = np.copy(Y)
        # Short all OTHER groups
        for oidx, other_key in enumerate(group_keys):
            if oidx == gidx:
                continue
            g = 1e9
            oki = all_nodes.index(other_key[0])
            okj = all_nodes.index(other_key[1])
            Y_cap[oki][oki] += g
            Y_cap[okj][okj] += g
            Y_cap[oki][okj] -= g
            Y_cap[okj][oki] -= g

        for i in range(n):
            Y_cap[i][i] += 1e-12

        I_vec = np.zeros(n)
        I_vec[ci] = 1.0
        I_vec[cj] = -1.0

        ref = 0
        Y_red = np.delete(np.delete(Y_cap, ref, axis=0), ref, axis=1)
        I_red = np.delete(I_vec, ref)

        try:
            V_red = np.linalg.solve(Y_red, I_red)
            V_full = np.insert(V_red, ref, 0.0)
            R_th = abs(V_full[ci] - V_full[cj])
            tau = R_th * C_total
            if tau > 1e-9 and tau < 1e5:
                taus.append(tau)
        except np.linalg.LinAlgError:
            pass

    try:
        from scipy.linalg import eig

        num_v = n
        num_i = len(inductors)
        size = num_v + num_i
        
        M_desc = np.zeros((size, size))
        N_desc = np.zeros((size, size))
        
        # M_desc top-left is C_mat
        C_mat = np.zeros((n, n))
        for cap in capacitors:
            ci = all_nodes.index(cap.node_id_1)
            cj = all_nodes.index(cap.node_id_2)
            C_mat[ci][ci] += cap.capacitance
            C_mat[cj][cj] += cap.capacitance
            C_mat[ci][cj] -= cap.capacitance
            C_mat[cj][ci] -= cap.capacitance
            
        M_desc[:n, :n] = C_mat
        
        # M_desc bottom-right is L_mat
        for k, ind in enumerate(inductors):
            M_desc[n+k, n+k] = ind.inductance
            
        # N_desc top-left is Y matrix (already computed as Y)
        N_desc[:n, :n] = Y
        
        # N_desc top-right is A_L and bottom-left is -A_L^T
        for k, ind in enumerate(inductors):
            ci = all_nodes.index(ind.node_id_1)
            cj = all_nodes.index(ind.node_id_2)
            
            # Current flows from node_id_1 to node_id_2
            N_desc[ci, n+k] += 1.0
            N_desc[cj, n+k] -= 1.0
            
            N_desc[n+k, ci] -= 1.0
            N_desc[n+k, cj] += 1.0

        # Remove reference node block
        ref = 0
        M_eig = np.delete(np.delete(M_desc, ref, axis=0), ref, axis=1)
        N_eig = np.delete(np.delete(N_desc, ref, axis=0), ref, axis=1)
        
        # General regularization for numerical stability
        for i in range(len(N_eig)):
            N_eig[i][i] += 1e-12
        
        # Solve generalized eigenvalue problem: N·X = λ·M·X
        eigenvalues, _ = eig(N_eig, M_eig)
        
        for ev in eigenvalues:
            if np.isfinite(ev) and abs(ev) > 1e-8:
                tau_ev = 1.0 / abs(ev)
                if tau_ev > 1e-12 and tau_ev < 1e5:
                    taus.append(tau_ev)
    except Exception:
        pass
            
    return max(taus) if taus else None