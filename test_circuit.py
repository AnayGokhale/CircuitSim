import sys
import os
sys.path.append(r"c:\Users\Anay\Python\CircuitSim")

from Physics import *
from Components import *

# Node 0 is Ground
# Node 1 is between Battery and Resistor
# Node 2 is between Resistor and Parallel Capacitors

bat = Battery(None, None, 1, 0, 9.0) # 9V battery
res = Resistor(None, None, 1, 2, 100.0, 0.0)
cap1 = Capacitor(None, None, 2, 0, 0.001, 0.0) # 1mF
cap2 = Capacitor(None, None, 2, 0, 0.001, 0.0) # 1mF

components = [bat, res, cap1, cap2]
active_nodes = [0, 1, 2]

matrix = generate_incidence_matrix(components, active_nodes)

print("Matrix:", matrix)

tau = calculate_time_constant(components)
print("Tau:", tau)

dt = tau / 60.0 if tau else 1/60.0
print("dt:", dt)

for i in range(5):
    volts, currents = ModifiedNodalAnalysis(matrix, components, active_nodes, dt)
    print(f"Step {i}: Volts={volts}, Currents={currents}")
    for c in components:
        if c.name == "Battery":
            print(f"  {c.name}: v={c.voltage}, i={c.current}")
        else:
            print(f"  {c.name}: v={c.voltage_drop}, i={c.current}")
