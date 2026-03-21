"""
Deep debugging: trace the MNA matrix construction for parallel caps
"""
import sys
import numpy as np
sys.path.append(r"c:\Users\Anay\Python\CircuitSim")

from Physics import *
from Components import *

# Reproduce the exact scenario from the Simulator:
# Battery -> Resistor -> two Capacitors in parallel back to ground
# This is the breadboard scenario where:
#   - Battery: node 1 -> 0 (ground)
#   - Resistor: node 1 -> 2
#   - Cap1: node 2 -> 0
#   - Cap2: node 2 -> 0

bat = Battery(None, None, 1, 0, 9.0)
res = Resistor(None, None, 1, 2, 100.0, 0.0)
cap1 = Capacitor(None, None, 2, 0, 0.001, 0.0)  # 1mF
cap2 = Capacitor(None, None, 2, 0, 0.001, 0.0)  # 1mF

components = [bat, res, cap1, cap2]
active_nodes = [0, 1, 2]

# Replicate the simulator's logic exactly (lines 1329-1346)
tau = calculate_time_constant(components)
print(f"Tau = {tau}")
print(f"Expected tau for R=100, C_eq=2mF: {100 * 0.002} = 0.2s")

dt_base = tau / 60.0 if tau else 1/60.0
print(f"dt_base = {dt_base}")

# The simulator does 10 substeps
substeps = 10
dt_sim = dt_base / substeps
print(f"dt_sim (per substep) = {dt_sim}")

matrix = generate_incidence_matrix(components, active_nodes)
print(f"\nIncidence matrix:\n{matrix}")

# Now simulate like the real simulator does (60 frames)
print(f"\n{'Frame':>5} {'sim_time':>10} {'V_cap1':>10} {'V_cap2':>10} {'I_res':>10} {'I_bat':>10} {'cap1_prev':>10} {'cap2_prev':>10}")
print("-" * 80)

sim_time = 0.0
for frame in range(120):
    for _ in range(substeps):
        volts, currents = ModifiedNodalAnalysis(matrix, components, active_nodes, dt=dt_sim)
    sim_time += dt_base
    
    if frame < 20 or frame % 20 == 0:
        print(f"{frame:5d} {sim_time:10.4f} {cap1.voltage_drop:10.6f} {cap2.voltage_drop:10.6f} "
              f"{res.current:10.6f} {bat.current:10.6f} {cap1._prev_voltage_drop:10.6f} {cap2._prev_voltage_drop:10.6f}")
    
    # Check for issues
    if any(np.isnan(volts)) or any(np.isinf(volts)):
        print(f">>> NaN/Inf at frame {frame}!")
        break
    if abs(cap1.voltage_drop) > 100 or abs(cap2.voltage_drop) > 100:
        print(f">>> Voltage explosion at frame {frame}!")
        break

# Expected steady state: both caps charge to 9V, current -> 0
print(f"\n--- Final state after {sim_time:.2f}s ---")
print(f"Cap1 voltage: {cap1.voltage_drop:.6f} V (expected: ~9V)")
print(f"Cap2 voltage: {cap2.voltage_drop:.6f} V (expected: ~9V)")
print(f"Resistor current: {res.current:.6f} A (expected: ~0A)")
print(f"Battery current: {bat.current:.6f} A (expected: ~0A)")

# Now check what happens with the incidence matrix sign conventions
print("\n\n=== SIGN CONVENTION CHECK ===")
print("Incidence matrix convention: -1 at node_id_1, +1 at node_id_2")
for i, c in enumerate(components):
    print(f"  {c.name}: node_id_1={c.node_id_1}, node_id_2={c.node_id_2}, row={matrix[i]}")

# The key question: when two capacitors have the SAME node pair,
# does the MNA system handle them correctly?
print("\n=== Checking capacitor _prev_voltage_drop sign ===")
# In MNA, v_drop = v1 - v2 for a component with incidence [-1, +1]
# For cap1: nodes 2->0, incidence is [1, 0, -1]
# So v_drop = V_node_id_1 - V_node_id_2 = V(2) - V(0) = V(2) - 0
# But V(2) is NEGATIVE in the solution! So v_drop is NEGATIVE.
# Then voltage_drop = abs(v_drop) but _prev_voltage_drop = v_drop (signed)
print(f"Cap1 _prev_voltage_drop: {cap1._prev_voltage_drop} (should be negative)")
print(f"Cap2 _prev_voltage_drop: {cap2._prev_voltage_drop} (should be negative)")
