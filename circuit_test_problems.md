# Component Verification Problems — Battery / Resistor / Capacitor / Inductor

Seven established textbook problems, one for every combination of {R, C, L} driven
by a Battery. Each lists the circuit exactly as you'd build it on the breadboard,
the published analytical solution, the source, and what the simulator should show.

Node 0 = ground. Values are in the simulator's SI units (V, Ω, F, H).
Every problem below was run through the project's own `Physics.ModifiedNodalAnalysis`
engine and matched the analytical answer to < 0.01% (see `validate.py`).

---

## 1 — Battery + Resistor (R): series–parallel network

**Source:** OpenStax *University Physics* Vol. 2, §10.3, "Resistors in Series and Parallel" (worked example).

**Build:** 50 V battery. R1 (10 Ω) and R2 (10 Ω) in series, then R3 (10 Ω) ∥ R4 (10 Ω) back to ground.

| Component | From node | To node | Value |
|-----------|-----------|---------|-------|
| Battery   | 0 | 1 | 50 V |
| R1        | 1 | 2 | 10 Ω |
| R2        | 2 | 3 | 10 Ω |
| R3        | 3 | 0 | 10 Ω |
| R4        | 3 | 0 | 10 Ω |

**Solution:** R_eq = 10 + 10 + (10‖10) = 25 Ω → I_total = 50/25 = **2.0 A**.
Parallel section drops 2.0 A × 5 Ω = **10 V**; each parallel leg carries **1.0 A**.

**Check:** battery current 2 A · I(R1) 2 A · I(R3) 1 A · V(R3) 10 V.

---

## 2 — Battery + Capacitor (C): DC steady state

**Source:** *All About Circuits*, DC vol., ch. 16 (a capacitor in DC steady state behaves as an open circuit); Q = CV, E = ½CV² are standard.

**Build:** 9 V battery across a 100 µF capacitor. (Put any small resistor — e.g. 1 Ω — in
series so the inrush current is well defined; it doesn't change the steady state.)

| Component | From | To | Value |
|-----------|------|----|-------|
| Battery   | 0 | 1 | 9 V |
| Capacitor | 1 | 0 | 100 µF |

**Solution:** at steady state the cap is fully charged → **V_C = 9 V**, **I → 0**,
Q = CV = **0.9 mC**, E = ½CV² = **4.05 mJ**.

**Check:** V_C settles to 9 V; current decays to ~0.

> ⚠️ An *ideal* source directly across an *ideal* capacitor (0 Ω loop) has an
> undefined instantaneous inrush current. V/Q/E are still correct; add series R for a clean current.

---

## 3 — Battery + Inductor (L): ideal current ramp

**Source:** Inductor constitutive law v_L = L (di/dt) → with constant V, i(t) = (V/L)·t (any circuits text, e.g. Nilsson & Riedel, *Electric Circuits*).

**Build:** 10 V battery across a 10 mH inductor.

| Component | From | To | Value |
|-----------|------|----|-------|
| Battery   | 0 | 1 | 10 V |
| Inductor  | 1 | 0 | 10 mH |

**Solution:** di/dt = V/L = 10 / 0.01 = **1000 A/s** (linear ramp). At 5 ms, i = **5 A**.

**Check:** inductor current rises linearly at 1000 A/s.

> ⚠️ Inductor current **sign** follows the engine's node-ordering convention
> (`normalize_bidirectional_components` orders nodes low→high). The magnitude is
> the physics; the sign just labels a reference direction.

---

## 4 — Battery + Resistor + Capacitor (RC): charging transient

**Source:** *All About Circuits*, DC vol., ch. 16, "Voltage and Current Calculations" (worked example: 15 V, 10 kΩ, 100 µF).

**Build:**

| Component | From | To | Value |
|-----------|------|----|-------|
| Battery   | 0 | 1 | 15 V |
| Resistor  | 1 | 2 | 10 kΩ |
| Capacitor | 2 | 0 | 100 µF |

**Solution:** τ = RC = **1.0 s**. v_C(t) = 15(1 − e^(−t/τ)).
At t = τ, v_C = 63.2% × 15 = **9.48 V**. At t = 7.25 s, v_C = **14.99 V**, I ≈ 1.07 µA.
Steady state: **V_C = 15 V, I → 0**.

**Check:** engine's own `calculate_time_constant` returns 1.0 s; v_C hits 9.48 V at 1 τ; settles to 15 V.

---

## 5 — Battery + Resistor + Inductor (RL): energizing transient

**Source:** OpenStax *College Physics*, §23.10, "RL Circuits" (end-of-section problem 6: 25 mH, 4 Ω, 12 V).

**Build:**

| Component | From | To | Value |
|-----------|------|----|-------|
| Battery   | 0 | 1 | 12 V |
| Resistor  | 1 | 2 | 4 Ω |
| Inductor  | 2 | 0 | 25 mH |

**Solution:** τ = L/R = **6.25 ms**. I(t) = (V/R)(1 − e^(−t/τ)), I_final = V/R = **3 A**.
At t = 12.5 ms (= 2τ), I = 3(1 − e^(−2)) = **2.59 A**.
Steady state: **I = 3 A, V_L = 0**.

**Check:** τ = 6.25 ms; |I| = 2.59 A at 2τ; |I| → 3 A; inductor voltage → 0.

---

## 6 — Battery + Inductor + Capacitor (LC): undamped oscillation

**Source:** LC resonant frequency f = 1/(2π√(LC)) (e.g. *University Physics* §14; Omni/Vedantu worked examples). Undamped series-LC step response oscillates about its final value with peak 2× (ζ = 0 second-order result).

**Build:** series L then C, no resistance.

| Component | From | To | Value |
|-----------|------|----|-------|
| Battery   | 0 | 1 | 10 V |
| Inductor  | 1 | 2 | 10 mH |
| Capacitor | 2 | 0 | 10 µF |

**Solution:** ω₀ = 1/√(LC) = **3162 rad/s**, f₀ = **503.3 Hz**, T = **1.987 ms**.
v_C(t) = V(1 − cos ω₀t) → oscillates **0 ↔ 20 V** forever (no damping), peaking at 2V = **20 V** at t = T/2.

**Check:** V_C peaks at 20 V; first peak at ~0.994 ms; period 1.987 ms (undamped — amplitude should not decay).

---

## 7 — Battery + Resistor + Inductor + Capacitor (RLC): damped step response

**Source:** Series-RLC step response — α = R/2L, ω₀ = 1/√(LC), ω_d = √(ω₀²−α²), ζ = α/ω₀ (standard; Nilsson & Riedel ch. 8; Testbook / Acadia lab worked forms).

**Build:** series R, L, C.

| Component | From | To | Value |
|-----------|------|----|-------|
| Battery   | 0 | 1 | 10 V |
| Resistor  | 1 | 2 | 20 Ω |
| Inductor  | 2 | 3 | 10 mH |
| Capacitor | 3 | 0 | 10 µF |

**Solution:** ω₀ = 3162 rad/s, α = R/2L = 1000 rad/s → α < ω₀ → **underdamped** (ζ = 0.316).
ω_d = √(ω₀²−α²) = **3000 rad/s**, f_d = **477.5 Hz**, damped period T_d = **2.094 ms**.
First-peak overshoot v_C = V(1 + e^(−απ/ω_d)) = **13.51 V**. Steady state: **V_C = 10 V, I → 0**.

**Check:** V_C overshoots to ~13.5 V, rings at 2.094 ms period with decaying amplitude, settles to 10 V.

---

### How to use this

- **Manual GUI test:** build each circuit on the breadboard, run it, and confirm the
  probe readouts match the "Check" line. This exercises placement, node detection,
  rendering, and physics for every component and combination.
- **Automated regression:** run `python3 validate.py` (uses the real `Physics.py`).
  Current result: **25/25 checks pass**.
