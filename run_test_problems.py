"""
Runs the 7 verification problems from circuit_test_problems.md against the
real Physics.py engine (no GUI) and compares simulator output against the
published analytical solutions. Read-only with respect to the engine: no
logic is modified, only exercised.

Components are built exactly as the tables in the markdown specify
(From = node_id_1, To = node_id_2). Per the doc's own note, component
sign follows the engine's node-ordering reference direction, so
comparisons are made on magnitudes.
"""
import sys
import os
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Components import Battery, Resistor, Capacitor, Inductor
from Physics import ModifiedNodalAnalysis, generate_incidence_matrix, calculate_time_constant

results = []


def check(label, expected, actual, tol_pct=1.0, abs_tol=None):
    """Compare |actual| against |expected|; tol_pct is percent tolerance.
    abs_tol used when expected is 0 (or near 0)."""
    exp_m = abs(expected)
    act_m = abs(actual)
    if abs_tol is not None and exp_m < 1e-30:
        ok = act_m <= abs_tol
        err_str = f"|actual|={act_m:.4e} (abs tol {abs_tol:.1e})"
    else:
        err = abs(act_m - exp_m) / exp_m * 100 if exp_m else float('inf')
        ok = err <= tol_pct
        err_str = f"err={err:.3f}% (tol {tol_pct}%)"
    status = "PASS" if ok else "FAIL"
    results.append((status, label, expected, actual, err_str))
    print(f"  [{status}] {label}: expected {expected:g}, got {actual:.6g}  ({err_str})")
    return ok


def reset(components):
    for c in components:
        c.current = 0.0
        if hasattr(c, 'voltage_drop'):
            c.voltage_drop = 0.0
        if hasattr(c, '_prev_voltage_drop'):
            c._prev_voltage_drop = 0.0
        if hasattr(c, '_prev_current'):
            c._prev_current = 0.0
        if hasattr(c, '_prev_voltage_drop_signed'):
            c._prev_voltage_drop_signed = 0.0


def step_to(components, active_nodes, inc, t_end, dt, sample=None):
    """Fixed-step transient from t=0 to t_end. Optionally records
    (t, sample(components)) each step."""
    trace = []
    t = 0.0
    n = int(round(t_end / dt))
    for _ in range(n):
        ModifiedNodalAnalysis(inc, components, active_nodes, dt=dt)
        t += dt
        if sample is not None:
            trace.append((t, sample(components)))
    return trace


def find_peaks(trace):
    """Local maxima of the traced magnitude signal: list of (t, value)."""
    peaks = []
    for i in range(1, len(trace) - 1):
        if trace[i][1] > trace[i - 1][1] and trace[i][1] >= trace[i + 1][1]:
            peaks.append(trace[i])
    return peaks


def header(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    results.append(("HEADER", title, None, None, None))


P = (0, 0)  # placeholder breadboard position, unused by the engine

# ---------------------------------------------------------------- Problem 1
header("Problem 1 - Battery + R network (50 V, R_eq = 25 ohm)")
bat = Battery(P, P, 0, 1, 50.0)
r1 = Resistor(P, P, 1, 2, 10.0, 0)
r2 = Resistor(P, P, 2, 3, 10.0, 0)
r3 = Resistor(P, P, 3, 0, 10.0, 0)
r4 = Resistor(P, P, 3, 0, 10.0, 0)
comps = [bat, r1, r2, r3, r4]
nodes = [0, 1, 2, 3]
reset(comps)
inc = generate_incidence_matrix(comps, nodes)
ModifiedNodalAnalysis(inc, comps, nodes, dt=1e-6)  # resistive: single solve
check("Battery current = 2.0 A", 2.0, bat.current)
check("I(R1) = 2.0 A", 2.0, r1.current)
check("I(R3) = 1.0 A", 1.0, r3.current)
check("V(R3) = 10 V", 10.0, r3.voltage_drop)

# ---------------------------------------------------------------- Problem 2
header("Problem 2 - Battery + C, DC steady state (9 V, 100 uF)")
# (a) exact build from the table: battery directly across capacitor
bat = Battery(P, P, 0, 1, 9.0)
cap = Capacitor(P, P, 1, 0, 100e-6, 0)
comps = [bat, cap]
nodes = [0, 1]
reset(comps)
inc = generate_incidence_matrix(comps, nodes)
step_to(comps, nodes, inc, t_end=2e-3, dt=1e-6)
check("V_C = 9 V (direct build)", 9.0, cap.voltage_drop)
q = cap.capacitance * cap.voltage_drop
check("Q = 0.9 mC", 0.9e-3, q)
e = 0.5 * cap.capacitance * cap.voltage_drop ** 2
check("E = 4.05 mJ", 4.05e-3, e)
i_direct = cap.current
print(f"  [INFO] I_C (direct, ideal-loop caveat in doc): {i_direct:.4e} A")

# (b) doc-recommended variant with 1 ohm series R for a well-defined current
bat = Battery(P, P, 0, 1, 9.0)
rs = Resistor(P, P, 1, 2, 1.0, 0)
cap = Capacitor(P, P, 2, 0, 100e-6, 0)
comps = [bat, rs, cap]
nodes = [0, 1, 2]
reset(comps)
inc = generate_incidence_matrix(comps, nodes)
step_to(comps, nodes, inc, t_end=2e-3, dt=1e-6)  # 20 tau
check("V_C = 9 V (with 1 ohm series R)", 9.0, cap.voltage_drop)
check("I -> 0 (with series R)", 0.0, cap.current, abs_tol=1e-6)

# ---------------------------------------------------------------- Problem 3
header("Problem 3 - Battery + L, current ramp (10 V, 10 mH)")
bat = Battery(P, P, 0, 1, 10.0)
ind = Inductor(P, P, 1, 0, 10e-3, 0)
comps = [bat, ind]
nodes = [0, 1]
reset(comps)
inc = generate_incidence_matrix(comps, nodes)
dt = 1e-6
trace = step_to(comps, nodes, inc, t_end=5e-3, dt=dt,
                sample=lambda cs: abs(cs[1].current))
check("|I_L| at t=5 ms = 5 A", 5.0, ind.current)
i_4ms = trace[int(4e-3 / dt) - 1][1]
i_5ms = trace[-1][1]
slope = (i_5ms - i_4ms) / 1e-3
check("di/dt = 1000 A/s (4->5 ms)", 1000.0, slope)

# ---------------------------------------------------------------- Problem 4
header("Problem 4 - RC charging (15 V, 10 kohm, 100 uF, tau = 1 s)")
bat = Battery(P, P, 0, 1, 15.0)
res = Resistor(P, P, 1, 2, 10e3, 0)
cap = Capacitor(P, P, 2, 0, 100e-6, 0)
comps = [bat, res, cap]
nodes = [0, 1, 2]
reset(comps)
tau = calculate_time_constant(comps)
check("calculate_time_constant = 1.0 s", 1.0, tau if tau else 0.0)
inc = generate_incidence_matrix(comps, nodes)
dt = 1e-3
step_to(comps, nodes, inc, t_end=1.0, dt=dt)
check("|V_C| at t=tau = 9.48 V", 15.0 * (1 - math.exp(-1)), cap.voltage_drop)
step_to(comps, nodes, inc, t_end=6.25, dt=dt)  # continue to t = 7.25 s
check("|V_C| at t=7.25 s = 14.99 V", 15.0 * (1 - math.exp(-7.25)), cap.voltage_drop)
check("|I| at t=7.25 s ~ 1.07 uA", 15.0 / 10e3 * math.exp(-7.25), cap.current, tol_pct=2.0)
step_to(comps, nodes, inc, t_end=10.0, dt=dt)  # far past settling
check("V_C steady state = 15 V", 15.0, cap.voltage_drop)
check("I steady state -> 0", 0.0, cap.current, abs_tol=1e-6)

# ---------------------------------------------------------------- Problem 5
header("Problem 5 - RL energizing (12 V, 4 ohm, 25 mH, tau = 6.25 ms)")
bat = Battery(P, P, 0, 1, 12.0)
res = Resistor(P, P, 1, 2, 4.0, 0)
ind = Inductor(P, P, 2, 0, 25e-3, 0)
comps = [bat, res, ind]
nodes = [0, 1, 2]
reset(comps)
tau = calculate_time_constant(comps)
check("calculate_time_constant = 6.25 ms", 6.25e-3, tau if tau else 0.0)
inc = generate_incidence_matrix(comps, nodes)
dt = 6.25e-6  # tau / 1000
step_to(comps, nodes, inc, t_end=12.5e-3, dt=dt)
check("|I| at t=2*tau = 2.59 A", 3.0 * (1 - math.exp(-2)), ind.current)
step_to(comps, nodes, inc, t_end=62.5e-3, dt=dt)  # continue 10 more tau
check("|I| steady state = 3 A", 3.0, ind.current)
check("V_L steady state -> 0", 0.0, ind.voltage_drop, abs_tol=1e-3)

# ---------------------------------------------------------------- Problem 6
header("Problem 6 - LC undamped oscillation (10 V, 10 mH, 10 uF)")
bat = Battery(P, P, 0, 1, 10.0)
ind = Inductor(P, P, 1, 2, 10e-3, 0)
cap = Capacitor(P, P, 2, 0, 10e-6, 0)
comps = [bat, ind, cap]
nodes = [0, 1, 2]
reset(comps)
inc = generate_incidence_matrix(comps, nodes)
T = 2 * math.pi * math.sqrt(10e-3 * 10e-6)  # 1.987 ms
dt = T / 2000.0
trace = step_to(comps, nodes, inc, t_end=3 * T, dt=dt,
                sample=lambda cs: abs(cs[2].voltage_drop))
peaks = find_peaks(trace)
big_peaks = [p for p in peaks if p[1] > 15.0]  # the ~20 V crests
if big_peaks:
    check("V_C first peak = 20 V", 20.0, big_peaks[0][1])
    check("first peak at t = 0.994 ms", T / 2, big_peaks[0][0])
    if len(big_peaks) >= 2:
        check("period = 1.987 ms", T, big_peaks[1][0] - big_peaks[0][0])
        check("no amplitude decay (peak 2 = peak 1)", big_peaks[0][1],
              big_peaks[1][1], tol_pct=0.5)
    if len(big_peaks) >= 3:
        check("no amplitude decay (peak 3 = peak 1)", big_peaks[0][1],
              big_peaks[2][1], tol_pct=0.5)
else:
    results.append(("FAIL", "V_C 20 V peaks not found", 20.0, 0.0, "no peaks"))
    print("  [FAIL] no ~20 V peaks found in V_C trace")

# ---------------------------------------------------------------- Problem 7
header("Problem 7 - series RLC step (10 V, 20 ohm, 10 mH, 10 uF)")
bat = Battery(P, P, 0, 1, 10.0)
res = Resistor(P, P, 1, 2, 20.0, 0)
ind = Inductor(P, P, 2, 3, 10e-3, 0)
cap = Capacitor(P, P, 3, 0, 10e-6, 0)
comps = [bat, res, ind, cap]
nodes = [0, 1, 2, 3]
reset(comps)
inc = generate_incidence_matrix(comps, nodes)
alpha = 20.0 / (2 * 10e-3)          # 1000 rad/s
w0 = 1 / math.sqrt(10e-3 * 10e-6)   # 3162 rad/s
wd = math.sqrt(w0 ** 2 - alpha ** 2)  # 3000 rad/s
Td = 2 * math.pi / wd               # 2.094 ms
dt = 1e-6
trace = step_to(comps, nodes, inc, t_end=10e-3, dt=dt,
                sample=lambda cs: abs(cs[3].voltage_drop))
peaks = find_peaks(trace)
big_peaks = [p for p in peaks if p[1] > 10.0]  # overshoot crests above final value
v_first_peak_expected = 10.0 * (1 + math.exp(-alpha * math.pi / wd))  # 13.51 V
if big_peaks:
    check("V_C first peak = 13.51 V", v_first_peak_expected, big_peaks[0][1])
    check("first peak at t = Td/2 = 1.047 ms", Td / 2, big_peaks[0][0])
    if len(big_peaks) >= 2:
        check("ringing period = 2.094 ms", Td, big_peaks[1][0] - big_peaks[0][0])
        # second overshoot peak: V(1 + e^(-alpha*3*pi/wd))
        v_second = 10.0 * (1 + math.exp(-alpha * 3 * math.pi / wd))
        check("second peak = 10.43 V (decaying)", v_second, big_peaks[1][1])
else:
    results.append(("FAIL", "V_C overshoot peaks not found", 13.51, 0.0, "no peaks"))
    print("  [FAIL] no overshoot peaks found in V_C trace")
check("V_C settles to 10 V", 10.0, cap.voltage_drop)
check("I settles to 0", 0.0, cap.current, abs_tol=1e-4)

# ---------------------------------------------------------------- summary
print(f"\n{'=' * 70}\nSUMMARY\n{'=' * 70}")
n_pass = sum(1 for r in results if r[0] == "PASS")
n_fail = sum(1 for r in results if r[0] == "FAIL")
for r in results:
    if r[0] == "HEADER":
        print(f"\n{r[1]}")
    else:
        print(f"  [{r[0]}] {r[1]}")
print(f"\nTOTAL: {n_pass} passed, {n_fail} failed out of {n_pass + n_fail} checks")
