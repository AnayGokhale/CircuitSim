import sys
import numpy as np
sys.path.append(r"c:\Users\Anay\Python\CircuitSim")

from Physics import *
from Components import *

print("=" * 70)
print("TEST 1: Single capacitor in series (should work)")
print("=" * 70)
# Battery(node1_hole, node2_hole, node_id_1, node_id_2, voltage)
# Resistor(node1_hole, node2_hole, node_id_1, node_id_2, resistance, voltage_drop)
# Capacitor(node1_hole, node2_hole, node_id_1, node_id_2, capacitance, voltage_drop)

bat1 = Battery(None, None, 1, 0, 9.0)
res1 = Resistor(None, None, 1, 2, 100.0, 0.0)
cap1_only = Capacitor(None, None, 2, 0, 0.001, 0.0)

components_series = [bat1, res1, cap1_only]
active_nodes_series = [0, 1, 2]

matrix_s = generate_incidence_matrix(components_series, active_nodes_series)
print("Incidence Matrix:")
print(matrix_s)

tau_s = calculate_time_constant(components_series)
dt_s = tau_s / 60.0 if tau_s else 1/60.0
print(f"Tau: {tau_s}, dt: {dt_s}")

for i in range(10):
    volts, currents = ModifiedNodalAnalysis(matrix_s, components_series, active_nodes_series, dt_s)
    print(f"  Step {i}: V_node2={volts[2]:.6f}, I_bat={currents[0]:.6f}, "
          f"cap_vdrop={cap1_only.voltage_drop:.6f}, cap_current={cap1_only.current:.6f}")

print()
print("=" * 70)
print("TEST 2: Two capacitors in PARALLEL (the problematic case)")
print("=" * 70)
# Reset components
bat2 = Battery(None, None, 1, 0, 9.0)
res2 = Resistor(None, None, 1, 2, 100.0, 0.0)
cap2a = Capacitor(None, None, 2, 0, 0.001, 0.0)  # 1mF
cap2b = Capacitor(None, None, 2, 0, 0.001, 0.0)  # 1mF

components_par = [bat2, res2, cap2a, cap2b]
active_nodes_par = [0, 1, 2]

matrix_p = generate_incidence_matrix(components_par, active_nodes_par)
print("Incidence Matrix:")
print(matrix_p)

tau_p = calculate_time_constant(components_par)
dt_p = tau_p / 60.0 if tau_p else 1/60.0
print(f"Tau: {tau_p}, dt: {dt_p}")

for i in range(10):
    volts, currents = ModifiedNodalAnalysis(matrix_p, components_par, active_nodes_par, dt_p)
    cap_v_sum = cap2a.voltage_drop + cap2b.voltage_drop
    print(f"  Step {i}: V_node2={volts[2]:.6f}, I_bat={currents[0]:.6f}, "
          f"cap2a_vdrop={cap2a.voltage_drop:.6f}, cap2a_i={cap2a.current:.6f}, "
          f"cap2b_vdrop={cap2b.voltage_drop:.6f}, cap2b_i={cap2b.current:.6f}, "
          f"res_vdrop={res2.voltage_drop:.6f}, res_i={res2.current:.6f}")
    
    # Check for NaN or explosion
    if any(np.isnan(volts)) or any(np.isinf(volts)):
        print("  >>> NaN/Inf detected! Stopping.")
        break
    if abs(volts[2]) > 1000:
        print(f"  >>> Voltage exploded to {volts[2]}! Stopping.")
        break

print()
print("=" * 70)
print("TEST 3: Analytical check - two 1mF caps in parallel = 2mF equivalent")
print("=" * 70)
bat3 = Battery(None, None, 1, 0, 9.0)
res3 = Resistor(None, None, 1, 2, 100.0, 0.0)
cap3 = Capacitor(None, None, 2, 0, 0.002, 0.0)  # 2mF (equivalent of 2x1mF parallel)

components_equiv = [bat3, res3, cap3]
active_nodes_equiv = [0, 1, 2]

matrix_e = generate_incidence_matrix(components_equiv, active_nodes_equiv)
tau_e = calculate_time_constant(components_equiv)
dt_e = tau_e / 60.0 if tau_e else 1/60.0
print(f"Tau: {tau_e}, dt: {dt_e}")

for i in range(10):
    volts, currents = ModifiedNodalAnalysis(matrix_e, components_equiv, active_nodes_equiv, dt_e)
    print(f"  Step {i}: V_node2={volts[2]:.6f}, I_bat={currents[0]:.6f}, "
          f"cap_vdrop={cap3.voltage_drop:.6f}, cap_current={cap3.current:.6f}")
