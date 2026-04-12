import sys
import os
import math
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Components import Wire, Battery, Resistor, Capacitor, Inductor, LED
from Physics import ModifiedNodalAnalysis, generate_incidence_matrix, calculate_time_constant

def create_component(c_type, node1, node2, **kwargs):
    if c_type == "Battery":
        return Battery((0,0), (0,0), node1, node2, kwargs['V'])
    elif c_type == "Resistor":
        return Resistor((0,0), (0,0), node1, node2, kwargs['R'], 0)
    elif c_type == "Capacitor":
        return Capacitor((0,0), (0,0), node1, node2, kwargs['C'], 0)
    elif c_type == "Inductor":
        return Inductor((0,0), (0,0), node1, node2, kwargs['L'], 0)
    return None

def run_simulation(name, components, active_nodes, is_lc=False, T=None):
    output = []
    output.append(f"=== Test: {name} ===")
    
    for c in components:
        c.current = 0.0
        if hasattr(c, '_prev_current'): c._prev_current = 0.0
        if hasattr(c, 'voltage_drop'): c.voltage_drop = 0.0
        if hasattr(c, '_prev_voltage_drop'): c._prev_voltage_drop = 0.0

    inc_matrix = generate_incidence_matrix(components, active_nodes)
    
    tau = calculate_time_constant(components)
    output.append(f"Calculated Tau (or 1/omega for LC): {tau}")

    def log_state(t, tag):
        output.append(f"\nTime: {t:.5e} s ({tag})")
        total_I = sum(np.abs(c.current) for c in components if c.name.startswith("Battery"))
        output.append(f"Total Current (from Battery): {total_I:.5e} A")
        
        for c in components:
            if c.name.startswith("Battery"):
                output.append(f"{c.name}: {c.voltage} V, {c.current:.5e} A")
            else:
                s = f"{c.name}: {c.voltage_drop:.5e} V, {c.current:.5e} A"
                if "Capacitor" in c.name or type(c) == Capacitor:
                    charge = c.capacitance * c.voltage_drop
                    s += f", Charge: {charge:.5e} C"
                elif "Inductor" in c.name or type(c) == Inductor:
                    energy = 0.5 * c.inductance * (c.current**2)
                    s += f", Energy: {energy:.5e} J"
                output.append(s)

    if not is_lc:
        target_t = 10 * tau if (tau and tau < 1e5) else 0.1
        dt = target_t / 1000.0 if (tau and tau < 1e5) else 1e-4

        ModifiedNodalAnalysis(inc_matrix, components, active_nodes, dt=1e-12)
        log_state(0, "t=0")
        
        t = 0
        for _ in range(1000):
            ModifiedNodalAnalysis(inc_matrix, components, active_nodes, dt=dt)
            t += dt
        
        log_state(t, "t=a lot relative to tau")

    else:
        period = 2 * math.pi * tau if tau else T
        if T: period = T
        dt = period / 1000.0
        
        ModifiedNodalAnalysis(inc_matrix, components, active_nodes, dt=1e-12)
        log_state(0, "t=0")
        
        t = 0
        steps = 1000
        
        for _ in range(250):
            ModifiedNodalAnalysis(inc_matrix, components, active_nodes, dt=dt)
            t += dt
        log_state(t, "t=T/4 (Peak component energy)")
        
        for _ in range(250):
            ModifiedNodalAnalysis(inc_matrix, components, active_nodes, dt=dt)
            t += dt
        log_state(t, "t=T/2 (Half oscillation)")
        
        for _ in range(250):
            ModifiedNodalAnalysis(inc_matrix, components, active_nodes, dt=dt)
            t += dt
        log_state(t, "t=3T/4 (Peak component energy)")
        
        for _ in range(250):
            ModifiedNodalAnalysis(inc_matrix, components, active_nodes, dt=dt)
            t += dt
        log_state(t, "t=T (Full oscillation)")

    output.append("\n" + "="*40 + "\n")
    return "\n".join(output)

results = []

# 1. Series Resistor Circuit
c1 = [
    create_component("Battery", 0, 1, V=10, name="Battery_10V"),
    create_component("Resistor", 1, 2, R=100, name="R1_100"),
    create_component("Resistor", 2, 0, R=200, name="R2_200"),
]
results.append(run_simulation("Circuit 1: Series Resistors", c1, [0, 1, 2], is_lc=False))

# 2. Parallel Resistor Circuit
c2 = [
    create_component("Battery", 0, 1, V=10, name="Battery_10V"),
    create_component("Resistor", 1, 0, R=100, name="R1_100"),
    create_component("Resistor", 1, 0, R=200, name="R2_200"),
]
results.append(run_simulation("Circuit 2: Parallel Resistors", c2, [0, 1], is_lc=False))

# 3. RC Circuits with combinations of series and parallel and with multiple of each component
c3 = [
    create_component("Battery", 0, 1, V=10, name="Battery_10V"),
    create_component("Resistor", 1, 2, R=50, name="R0_50"),
    create_component("Resistor", 2, 3, R=100, name="R1_100"),
    create_component("Capacitor", 2, 3, C=10e-6, name="C1_10uF"),
    create_component("Resistor", 3, 0, R=200, name="R2_200"),
    create_component("Capacitor", 3, 0, C=20e-6, name="C2_20uF"),
    create_component("Resistor", 2, 0, R=300, name="R3_300"),
    create_component("Capacitor", 2, 0, C=30e-6, name="C3_30uF"),
]
results.append(run_simulation("Circuit 3: RC Series and Parallel Mixed", c3, [0, 1, 2, 3], is_lc=False))

# 4. RL Circuits with combinations of series and parallel and with multiple of each component
c4 = [
    create_component("Battery", 0, 1, V=10, name="Battery_10V"),
    create_component("Resistor", 1, 2, R=50, name="R0_50"),
    create_component("Resistor", 2, 3, R=100, name="R1_100"),
    create_component("Inductor", 2, 3, L=10e-3, name="L1_10mH"),
    create_component("Resistor", 3, 0, R=200, name="R2_200"),
    create_component("Inductor", 3, 0, L=20e-3, name="L2_20mH"),
    create_component("Resistor", 2, 0, R=300, name="R3_300"),
    create_component("Inductor", 2, 0, L=30e-3, name="L3_30mH"),
]
results.append(run_simulation("Circuit 4: RL Series and Parallel Mixed", c4, [0, 1, 2, 3], is_lc=False))

# 5. LC circuits with combinations of series and parallel and with multiple of each component
c5 = [
    create_component("Battery", 0, 1, V=10, name="Battery_10V"),
    create_component("Capacitor", 1, 2, C=10e-6, name="C1_10uF"), # Series blocking capacitor ensures oscillation
    create_component("Inductor", 2, 3, L=10e-3, name="L1_10mH"),
    create_component("Capacitor", 2, 3, C=20e-6, name="C2_20uF"),
    create_component("Inductor", 3, 0, L=20e-3, name="L2_20mH"),
    create_component("Capacitor", 3, 0, C=30e-6, name="C3_30uF"),
    create_component("Inductor", 2, 0, L=30e-3, name="L3_30mH"),
]
T5 = 2 * math.pi * math.sqrt(10e-3 * 10e-6)
results.append(run_simulation("Circuit 5: LC Series and Parallel Mixed", c5, [0, 1, 2, 3], is_lc=True, T=T5))

# 6. RLC circuits with combinations of series and parallel and with multiple of each component
c6 = [
    create_component("Battery", 0, 1, V=10, name="Battery_10V"),
    create_component("Resistor", 1, 2, R=50, name="R0_50"),
    create_component("Resistor", 2, 3, R=100, name="R1_100"),
    create_component("Inductor", 2, 3, L=10e-3, name="L1_10mH"),
    create_component("Capacitor", 2, 3, C=10e-6, name="C1_10uF"),
    create_component("Resistor", 3, 0, R=200, name="R2_200"),
    create_component("Inductor", 3, 0, L=20e-3, name="L2_20mH"),
    create_component("Capacitor", 3, 0, C=20e-6, name="C2_20uF"),
    create_component("Resistor", 2, 0, R=300, name="R3_300"),
    create_component("Inductor", 2, 0, L=30e-3, name="L3_30mH"),
    create_component("Capacitor", 2, 0, C=30e-6, name="C3_30uF"),
]
results.append(run_simulation("Circuit 6: RLC Series and Parallel Mixed", c6, [0, 1, 2, 3], is_lc=False))

with open("circuit_test_results.txt", "w") as f:
    f.write("\n".join(results))

print("Testing complete. Results saved in circuit_test_results.txt")
