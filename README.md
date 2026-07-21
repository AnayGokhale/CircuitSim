# Circuit Simulator

A high-fidelity Python based circuit simulator that provides an interactive breadboard visualization alongside an accurate underlying physics engine. The application enables users to build, analyze, and test various circuit configurations, handling components from simple resistors to complex mixed-signal LC and RLC networks. 

Built using Pygame for rendering and configured to compile to WebAssembly via Pygbag, the simulator can run natively as a desktop application or embedded directly in a web browser.

<img width="950" height="550" alt="Screenshot 2026-07-21 150958" src="https://github.com/user-attachments/assets/da503f5e-490e-4706-8131-d6efaccd68db" />


## Core Features

### Advanced Physics Engine
The simulation backend relies on Modified Nodal Analysis (MNA) coupled with trapezoidal numerical integration to ensure strict numerical stability and physical accuracy. The physics model supports:
*   Real-time analysis of transient and steady-state behavior for RC, RL, LC, and RLC circuits.
*   Precise charge and energy conservation calculations over time.
*   Automatic detection of time constants and oscillation frequencies in LC circuits.
*   Accurate parallel and series configuration handling, avoiding singular matrix mathematical errors in extreme edge cases like zero resistance or shorted inductors.

### Interactive Breadboard Visualization
Rather than using basic placeholder images, the simulator renders detailed procedural models of electronic components directly onto an interactive breadboard.
*   **Dynamic Visuals**: Resistors dynamically draw standard color bands matching their user defined ohmic values. LEDs alter their visual brightness based on calculated power dissipation and turn off completely when the simulation stops.
*   **Custom Graphics**: Features sophisticated programmatic drawings for batteries and toroidal inductors, with careful attention paid to visual contrast, shadows, and component scaling against the breadboard background.

<img width="245" height="150" alt="Screenshot 2026-07-21 151334" src="https://github.com/user-attachments/assets/98bd6b45-dc74-4c84-96b4-d8a866320c4d" />
<img width="245" height="150" alt="Screenshot 2026-07-21 151304" src="https://github.com/user-attachments/assets/8b39f02f-d3cc-4978-90dd-10e9bbfbe788" />
<img width="245" height="150" alt="Screenshot 2026-07-21 151127" src="https://github.com/user-attachments/assets/d95a75a4-7821-46bf-914f-de3b1f73aedd" />
<img width="245" height="150" alt="Screenshot 2026-07-21 151533" src="https://github.com/user-attachments/assets/ebcb317b-ab07-463e-aa34-fe41df29c4cc" />

### Comprehensive Verification Suite
The project includes a robust testing module that strictly validates the physics calculations. The tests simulate complex scenarios like ringing in an LC circuit or discharge curves in an RC circuit. These tests generate detailed logs recording voltages, currents, and component energy at initial states, peak oscillations, and steady states.

## Supported Components

*   **Wiring and Power**: Node to node wires and DC voltage sources.
*   **Resistors**: Static resistance models with dynamic color banding.
*   **Capacitors**: Models charge accumulation, transient voltage drops, and initial conditions.
*   **Inductors**: Predicts current inertia and voltage spikes across dynamic networks.
*   **LEDs**: Calculates current limitations and power boundaries for accurate brightness simulation.

## Architecture and Web Support

The project is structured into three primary modular components.
*   `Physics.py`: Houses the MNA implementation, the trapezoidal rule handlers, and matrix generation routines.
*   `Components.py`: Defines the data classes and behaviors for every supported physical part.
*   `main.py`: Serves as the primary Pygame loop and UI controller. The main entry point acts as an asynchronous wrapper allowing the application event loop to run cleanly with `pygbag`.

By utilizing `pygbag`, the entire Python suite can be compiled to execute locally within any standard web browser, making it trivial to host and share the simulator online.

## LICENSE
Copyright 2026 Anay Gokhale

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
