# DETAILED THEORY MANUAL · MARS: Modal Analysis Response Solver

> **Audience**  
> Practicing mechanical and structural engineers using MARS to post-process modal analysis data.
>
> **Goal**  
> Explain, in a teaching-oriented manner, the continuum mechanics and structural dynamics theory that informs each type of result presented by MARS so that users can interpret outputs confidently and communicate engineering findings.

---

## 1. How to Use This Manual

This guide complements the user manuals by digging into the **physics behind the numbers**. You do not need to understand Python, PyQt, or the software internals. Instead, focus on:

- **What each dataset represents** (modal coordinates, stress modes, deformation modes, steady-state loads).
- **Which assumptions are inherent** (linearity, proportional damping, small deformations).
- **How the solver converts modal information into engineering quantities** (displacements, stresses, fatigue metrics).
- **How to verify and interpret results** using simple checks rooted in classical theory.

Keep the manual nearby when reviewing solver outputs or preparing reports. Each section ends with a short checklist that you can apply to your own models.

---

## 2. Foundations of Modal Analysis

### 2.1 Equation of Motion

For a linear structure with `n` physical degrees of freedom, the familiar matrix equation is:

```
M r̈(t) + C ṙ(t) + K r(t) = f(t)
```

- `M` – Mass matrix (positive definite)  
- `C` – Damping matrix (often assumed Rayleigh/proportional)  
- `K` – Stiffness matrix  
- `r(t)` – Physical displacement vector  
- `f(t)` – External force vector

We assume **small displacements** and **linear material behavior**, which allows superposition and uncoupling of modes.

### 2.2 Modal Decomposition

Solving the undamped eigenvalue problem

```
K Φ = M Φ Λ
```

produces a modal matrix `Φ = [φ₁, φ₂, …, φ_n]` and diagonal matrix of squared natural frequencies `Λ = diag(ω₁², …, ω_n²)`.

Common practice mass-normalizes the modes:

```
Φᵀ M Φ = I
```

This rotation simplifies the equations of motion in modal coordinates `q(t)` to:

```
q̈(t) + 2 ζ Λ½ q̇(t) + Λ q(t) = Φᵀ f(t)
```

where `ζ` contains modal damping ratios. Integrating these uncoupled scalar ODEs (outside of MARS) yields the **modal coordinate histories** that arrive in the `.mcf` file.

### 2.3 Checklist

- [ ] Model is linear and solved with a modal method.  
- [ ] Modes are mass-normalized (typical in commercial FEA exports).  
- [ ] Time step used for modal integration is fine enough to capture the highest retained natural frequency (≥ 20 samples per period recommended).

---

## 3. Understanding the Input Packages

MARS consumes several complementary datasets:

| Dataset | Physical Meaning | Typical Source |
| --- | --- | --- |
| Modal coordinates (`.mcf`) | `q_i(t)` – participation amplitude of each retained mode over time | Transient modal superposition run |
| Modal stresses (`.csv`) | `Φσ` – stress “shapes” per mode at each node | Modal post-processing, e.g. ANSYS “modal stress” export |
| Modal deformations (`.csv`, optional) | `Φu` – displacement shapes per mode | Same as above or neutral file |
| Steady-state stress (`.txt`, optional) | Static bias stresses (therm, preload, etc.) | Static analysis or service load case |

**Key assumption**: Node ordering is consistent across all files. The solver aligns data by node ID.

### Interpretation Tip

Think of modal stress entries `σ_{x, mode 3, node 57}` as the stress contribution at node 57 when mode 3 vibrates at unit amplitude. The modal coordinate `q_3(t)` then scales this contribution in time.

---

## 4. Reconstructing Physical Displacements

### 4.1 Modal Superposition for Displacements

Once the modal coordinates are known, physical displacements follow:

```
r(t) = Φ q(t)
```

In component form for node `i` in direction `x`:

```
u_i(t) = Σ_{k=1}^{n_modes} φ_{i,k} q_k(t)
```

### 4.2 Velocity and Acceleration

Time derivatives are obtained numerically. Central differences (fourth-order in the interior) approximate:

```
u̇_i(t_k) ≈ (-u_{i,k+2} + 8u_{i,k+1} - 8u_{i,k-1} + u_{i,k-2}) / (12 Δt)
```

```
ü_i(t_k) ≈ (-u_{i,k+2} + 16u_{i,k+1} - 30u_{i,k} + 16u_{i,k-1} - u_{i,k-2}) / (12 Δt²)
```

Magnitude outputs (`||u||`, `||u̇||`, `||ü||`) provide an envelope for each node.

### 4.3 Engineering Use

- Check peak displacement against allowable limits (clearances, serviceability).  
- Derive base shear/forces if stiffness is known.  
- Export velocity for initial-condition transfer to explicit solvers.

### Checklist

- [ ] Modal coordinates are long enough to span the dynamic event.  
- [ ] Time step uniformity verified (irregular spacing reduces derivative accuracy).  
- [ ] Deformation scale in visualization kept within small-strain assumptions.

---

## 5. Stress Recovery Theory

### 5.1 Modal Stress Fields

Just as displacements are recovered with `Φu`, stresses arise from `Φσ`:

```
σ_component(t) = Φσ_component q(t)
```

Each stress component (σₓ, σ_y, σ_z, τ_xy, τ_yz, τ_xz) has its own modal matrix. MARS performs the matrix multiplications and returns a full stress time history per node.

### 5.2 Steady-State Bias

If a static stress field (thermal preload, assembly stress) exists, it is added after modal reconstruction:

```
σ_total(t) = σ_modal(t) + σ_static
```

### 5.3 Principal Stresses

Principal stresses are eigenvalues of the symmetric stress tensor. For a 3D state:

1. Compute invariants  
   ```
   I₁ = σx + σy + σz
   I₂ = σxσy + σyσz + σzσx - τxy² - τyz² - τxz²
   I₃ = σxσyσz + 2 τxy τyz τxz - σx τyz² - σy τxz² - σz τxy²
   ```
2. Solve the cubic equation `λ³ - I₁ λ² + I₂ λ - I₃ = 0`.  
3. Order results such that `s₁ ≥ s₂ ≥ s₃`.

`s₁` (max principal) and `s₃` (min principal) highlight tension/compression extremes.

### 5.4 Von Mises Stress

Von Mises stress represents distortion energy. Using stress components:

```
σ_vm = √(0.5[(σx - σy)² + (σy - σz)² + (σz - σx)²] + 3[τxy² + τyz² + τxz²])
```

In strain energy terms, yielding begins when `σ_vm` equals the material’s yield strength (for ductile isotropic metals).

### 5.5 Interpretation Tips

- Compare `σ_vm` envelopes to allowable stress (yield/ultimate divided by safety factor).  
- Plot `s₁` and `s₃` to locate tensile/compressive hot spots.  
- Inspect `σ_total` at critical timestamps (e.g., peaks reported by MARS).

### Checklist

- [ ] Units of modal stress data match design units (MPa, psi).  
- [ ] Steady-state file (if used) corresponds to the same node ordering.  
- [ ] Principal stresses used for brittle materials or plane-stress fracture checks.

---

## 6. Damping, Loading, and Modal Truncation Considerations

### 6.1 Damping

Modal damping ratios `ζ` dictate how fast a mode’s response decays. If you do not export damping, many solvers assume Rayleigh damping:

```
C = α M + β K
```

The corresponding modal damping ratio is:

```
ζ_i = (α / 2ω_i) + (β ω_i / 2)
```

Ensure the exported modal coordinates were integrated with damping values representative of your structure; MARS does not modify them.

### 6.2 Loading

Modal superposition assumes load distribution can be projected onto each mode:

```
Φᵀ f(t) = generalised force history
```

For base acceleration (seismic) problems, this projection involves mass participation factors. Confirm that the upstream solution captured the correct loading.

### 6.3 Mode Truncation

Only a finite number of modes are kept. Dropping higher modes reduces accuracy at high frequencies. Rules of thumb:

- Retain modes up to at least 1.5× the highest significant forcing frequency.  
- Check modal effective mass to ensure cumulative participation > 90% in each direction.  
- Use the **skip modes** option cautiously—skipping too many can degrade accuracy around resonance.

---

## 7. Fatigue and Damage Assessment

### 7.1 Rainflow Counting

Rainflow counting converts a stress-time history into stress ranges and cycle counts. The method mimics how a hysteresis loop “rainflows” through turning points, aligning with ASTM E1049-85.

Given a signed von Mises history `σ_vm,sign(t)`:

- Peaks and valleys define half-cycles.  
- Matching exit and entry points produce full cycles with range `Δσ`.  
- Residual half-cycles are counted with weight 0.5.

### 7.2 Miner’s Rule

For an S-N curve `Δσ^m N = A`, the allowable cycle count at range `Δσ` is:

```
N_fail = A / (Δσ)^m
```

Damage per cycle is `1 / N_fail`. The cumulative damage per node:

```
D = Σ (n_cycle / N_fail)
```

When `D` approaches 1, fatigue failure is expected. This is a **linear damage accumulation** model—conservative when load sequences vary greatly.

### 7.3 Practical Advice

- Ensure the material constants `A` and `m` are entered in units consistent with stress data.  
- Consider mean stress effects separately if significant (signed von Mises is a proxy, but Goodman/Gerber corrections may be needed for high mean stress).  
- Validate damage hotspots by examining the dominant frequency content; consider spectrum-based methods for complex loadings.

---

## 8. Active Plasticity Correction Methods

### 8.1 The Notch Problem: Why Elastic Stresses Overpredict Reality

Modal analysis yields **elastic** stresses that assume linear material behavior. At stress concentrations (notches, fillets, holes), the elastic stress field can locally exceed yield. In reality, plastic flow redistributes stress and reduces peak values. Reporting elastic stress at notches therefore overpredicts the actual stress and may mislead fatigue assessments.

**Plasticity correction methods** address this by computing a reduced, **plastically corrected stress** and an associated **plastic strain** using notch-root approximations. These methods rely on the observation that the elastic stress-strain product (proportional to strain energy) must equal the sum of elastic plus plastic energy in the real material.

MARS implements three correction methods:

1. **Neuber's Rule** (peak-value, scalar)  
2. **Glinka's Energy-Density Method** (peak-value, scalar)  
3. **Incremental Buczynski–Glinka (IBG)** (time-history, tensor) — *currently experimental*

All three incorporate **temperature-dependent material hardening curves** to handle spatially varying thermal fields typical of aerospace and power-generation components.

---

### 8.2 Neuber's Rule

#### 8.2.1 Classical Formulation

Neuber's rule states that the product of the elastic stress concentration factor and the elastic strain concentration factor equals the square of the theoretical (elastic) stress concentration factor:

\[
K_\sigma \cdot K_\varepsilon = K_t^2
\]

For a notch root, this translates to:

\[
\frac{\sigma}{\sigma_{\text{nom}}} \cdot \frac{\varepsilon}{\varepsilon_{\text{nom}}} = \left(\frac{\sigma_e}{\sigma_{\text{nom}}}\right)^2
\]

where:
- \(\sigma_e\) = elastic (uncorrected) stress at the notch  
- \(\sigma\) = true (corrected) stress accounting for plasticity  
- \(\varepsilon\) = true total strain \(= \sigma / E + \varepsilon_p\)  

Simplifying, Neuber's rule becomes:

\[
\sigma \cdot \left(\frac{\sigma}{E} + \varepsilon_p(\sigma)\right) = \frac{\sigma_e^2}{E}
\]

This is a **nonlinear algebraic equation** in \(\sigma\) because plastic strain \(\varepsilon_p\) depends on \(\sigma\) via the material's **cyclic stress-strain curve** (or multilinear hardening table).

#### 8.2.2 Solving the Neuber Equation

MARS uses a **Newton-Raphson iterative solver** (see `solve_neuber_vector_core` in `src/solver/plasticity_engine.py`):

1. Start with an initial guess \(\sigma_0 = \min(\sigma_e, \sigma_y(T))\) where \(\sigma_y(T)\) is the temperature-dependent yield.  
2. At each iteration \(i\):
   - Compute \(\varepsilon_p(\sigma_i)\) by interpolating the hardening curve at the current temperature \(T\).  
   - Evaluate residual \(r(\sigma) = \frac{\sigma}{E} + \varepsilon_p(\sigma) - \frac{\sigma_e^2}{\sigma \cdot E}\).  
   - Compute numerical derivative \(r'(\sigma)\) via finite difference.  
   - Update \(\sigma_{i+1} = \sigma_i - r / r'\).  
3. Stop when \(|r| / |\sigma| < \text{tol}\) or maximum iterations reached.

Temperature-dependence enters via:
- Young's modulus \(E(T)\)  
- Yield stress \(\sigma_y(T)\)  
- Hardening curve \(\sigma(\varepsilon_p, T)\)  

all linearly interpolated between user-provided temperature rows.

#### 8.2.3 When to Use Neuber

- **Ductile metals** with well-defined cyclic stress-strain behavior.  
- **Peak-value assessments** (max stress over a time history).  
- **Proportional loading** where stress components maintain fixed ratios.  
- Situations where notch-root plasticity is expected to be **local and confined**.

---

### 8.3 Glinka's Energy-Density Method

#### 8.3.1 Energy Equality Principle

Glinka's method equates **total strain energy density** rather than stress×strain directly. The elastic strain energy density at the notch is:

\[
U_e^{\text{elastic}} = \frac{\sigma_e^2}{2E}
\]

In the real (elastic-plastic) material, total strain energy density is:

\[
U_{\text{total}} = U_e^{\text{corrected}} + U_p = \frac{\sigma^2}{2E} + \int_0^{\varepsilon_p(\sigma)} \sigma_{\text{flow}}(\varepsilon_p') \, d\varepsilon_p'
\]

The correction principle is:

\[
\frac{\sigma^2}{2E} + U_p(\sigma, T) = \frac{\sigma_e^2}{2E}
\]

where \(U_p(\sigma, T)\) is the **plastic strain energy** accumulated up to stress \(\sigma\) at temperature \(T\).

#### 8.3.2 Computing Plastic Strain Energy

The plastic energy integral is evaluated via **trapezoidal rule** over the piecewise-linear hardening curve:

\[
U_p = \sum_{k=1}^{n} \frac{1}{2} \left(\sigma_k + \sigma_{k-1}\right) \left(\varepsilon_{p,k} - \varepsilon_{p,k-1}\right)
\]

For stresses beyond the last curve point, linear extrapolation is applied (or plateau mode if selected).

#### 8.3.3 Solving the Glinka Equation

Similar to Neuber, an iterative solver finds \(\sigma\) such that:

\[
r(\sigma) = \frac{\sigma^2}{2E} + U_p(\sigma, T) - \frac{\sigma_e^2}{2E} = 0
\]

The derivative is computed numerically, and Newton iterations proceed until convergence.

#### 8.3.4 When to Use Glinka

- Preferred when **energy-based fatigue models** (e.g., Smith-Watson-Topper, strain-life) are used.  
- More physically consistent for **nonproportional loading** or complex multiaxial states (when used with equivalent stress measures).  
- Generally **more conservative** than Neuber for highly notched geometries because it accounts for the full hardening curve shape.

---

### 8.4 Incremental Buczynski–Glinka (IBG) Method

#### 8.4.1 Motivation for Time-History Correction

Neuber and Glinka apply to **peak values**. For time-varying stress histories (e.g., transient thermal-mechanical cycles), a single peak correction may not capture:
- **Plasticity accumulation** over multiple cycles  
- **Loading path dependence** (load-unload hysteresis)  
- **Full tensor state** at each time step

The **Incremental Buczynski–Glinka (IBG)** method extends Glinka's energy principle to a **step-by-step, tensor-aware** framework.

#### 8.4.2 Incremental Energy Balance

At each time step \(k\), the elastic strain energy increment is:

\[
\Delta U_e^{\text{elastic}} = \frac{1}{2} \left(\boldsymbol{\sigma}_k^e + \boldsymbol{\sigma}_{k-1}^e\right) : \left(\boldsymbol{\varepsilon}_k^e - \boldsymbol{\varepsilon}_{k-1}^e\right)
\]

In von Mises (J₂) plasticity, only the **deviatoric part** contributes to plastic flow. The IBG algorithm:

1. Computes \(\Delta U_e\) from the deviatoric components.  
2. Solves for the **incremental plastic strain** \(\Delta \varepsilon_p\) via:

\[
\Delta U_e = \int_{\varepsilon_{p,k-1}}^{\varepsilon_{p,k}} \sigma_{\text{flow}}(\varepsilon_p, T) \, d\varepsilon_p
\]

3. Accumulates total plastic strain: \(\varepsilon_{p,k} = \varepsilon_{p,k-1} + \Delta \varepsilon_p\).  
4. Computes a **radial scaling factor** \(s\) to reduce the deviatoric stress:

\[
s = \frac{1}{1 + E \varepsilon_{p,k} / \max(\sigma_{\text{vm}}^{\text{corr}}, \sigma_{\text{flow}})}
\]

5. Applies scaling **only to the deviatoric part**, preserving hydrostatic (mean) stress:

\[
\boldsymbol{\sigma}_k^{\text{corr}} = \boldsymbol{\sigma}_k^{\text{hydro}} + s \cdot \boldsymbol{\sigma}_k^{\text{dev}}
\]

This tensor update is repeated for all time steps, producing a **corrected stress history** and **plastic strain history**.

#### 8.4.3 Status in MARS

**⚠️ IBG is currently DISABLED** at the UI level. While the core algorithm (`ibg_solver_tensor_core`) is implemented, it is **greyed out** in the plasticity method dropdown pending:
- Further validation against transient FEA benchmarks  
- Robustness improvements (convergence, numerical stability)  
- Tuning of the empirical \(k\)-factor used in energy partitioning

See `PLASTICITY_INTEGRATION_PLAN.md` for details on future re-enablement.

#### 8.4.4 When IBG Will Be Appropriate (Future)

- **Transient thermal-mechanical cycles** with significant plasticity at each step.  
- **Multiaxial nonproportional loading** where tensor history matters.  
- **Ratcheting or shakedown assessment** requiring accumulated strain tracking.

---

### 8.5 Temperature-Dependent Material Curves

#### 8.5.1 Material Database Structure

All three methods rely on a **multilinear hardening database** (`MaterialDB` in `src/solver/plasticity_engine.py`) that stores:

| Array | Shape | Description |
|-------|-------|-------------|
| `TEMP` | `(NT,)` | Temperatures in ascending order |
| `E_tab` | `(NT,)` | Young's modulus at each temperature |
| `SIG` | `(NT, NP)` | True stress values (NP points per curve) |
| `EPSP` | `(NT, NP)` | Plastic strain values corresponding to `SIG` |

Each row defines a **piecewise-linear hardening curve** at a specific temperature. The first point in each curve approximates **yield** (\(\varepsilon_p \approx 0\)).

#### 8.5.2 Temperature Interpolation

For a node at temperature \(T\):

1. Locate bracketing temperatures: \(T_i \leq T < T_{i+1}\).  
2. Compute linear weight: \(w = (T - T_i) / (T_{i+1} - T_i)\).  
3. Blend properties:

\[
E(T) = (1 - w) E_i + w E_{i+1}
\]

\[
\sigma(\varepsilon_p, T) = (1 - w) \sigma_i(\varepsilon_p) + w \sigma_{i+1}(\varepsilon_p)
\]

This ensures smooth variation across the thermal field.

#### 8.5.3 Extrapolation Modes

Beyond the last point of a hardening curve, MARS offers two modes:

- **Linear extrapolation** (default): Continue the slope from the last two points. Suitable for strain-hardening alloys.  
- **Plateau**: Clamp stress to the last value. Suitable for perfectly plastic or limited-hardening materials.

Select the mode via the **Extrapolation Mode** option in the Material Profile dialog.

---

### 8.5.4 Iteration Control Parameters

The Newton-Raphson solver for Neuber and Glinka equations exposes two tuning parameters:

#### Max Iterations
- **Default**: 60
- **Range**: 1 to 10,000
- **Purpose**: Limits the number of iteration steps before declaring non-convergence
- **When to increase**: If console shows "failed to converge" warnings at nodes with extreme stress concentrations or near phase-change temperatures
- **Trade-off**: Higher values increase robustness but may slow down computation

#### Tolerance
- **Default**: 1×10⁻¹⁰
- **Range**: 0.0 to 1.0 (scientific notation accepted)
- **Purpose**: Defines the relative residual threshold for convergence: |r(σ)| / |σ| < tol
- **When to relax**: For noisy FEA data or when solver oscillates near convergence
- **Trade-off**: Looser tolerance speeds convergence but may reduce accuracy of corrected stress and plastic strain by 0.1-1%

A warning label appears in the UI if either parameter is changed from default, reminding users that relaxed settings may impact accuracy.

---

### 8.6 Practical Workflow in MARS

#### 8.6.1 Enabling Plasticity Correction

On the **Main Window (Solver) tab**:

1. Tick **Plasticity Correction**.  
2. Select a method: **Neuber**, **Glinka**, or ~~Incremental Buczynski-Glinka (IBG)~~ (greyed out).  
3. Click **Enter Material Profile** to define hardening curves at multiple temperatures.  
4. Load a **Temperature Field File** (CSV with NodeID and Temperature columns) to assign \(T\) to each node.  
5. (Optional) Adjust **Max Iterations** and **Tolerance** for solver tuning.  
6. Ensure **Von Mises Stress** output is selected (plasticity correction operates on von Mises equivalent stress).

#### 8.6.2 Material Profile Dialog

- Enter temperature values (in consistent units, e.g., °C).  
- For each temperature, specify pairs of **(True Stress, Plastic Strain)**.  
- First point defines approximate yield; subsequent points trace the hardening curve.  
- Choose **Extrapolation Mode** based on material behavior beyond the curve.

**Data Entry Tips:**
- Use data from **cyclic stress-strain tests** (not monotonic tensile), as plasticity correction applies to fatigue scenarios
- Typical datasets: 3-5 temperature points, 5-15 stress-strain pairs per temperature
- For high-temperature alloys: span operational range (e.g., 25°C to 650°C for Ni-based superalloys)
- If only monotonic data available, use with caution and validate against nonlinear FEA

#### 8.6.3 Temperature Field File

The temperature field file assigns a nodal temperature for material property interpolation:

**Format Requirements:**
- **File type**: CSV (comma-separated values), not tab-delimited .txt despite the button label
- **Required columns**: `NodeID`, `Temperature`
- **Optional columns**: Ignored (e.g., X, Y, Z coordinates are allowed but unused)
- **Node coverage**: Every node in the modal stress file must have a temperature entry; missing nodes trigger an error
- **Units**: Must match temperature units in Material Profile (typically °C or K)

**Example File:**
```csv
NodeID,Temperature
1001,25.0
1002,150.5
1003,300.0
1004,300.0
1005,275.2
```

**Common Mistakes:**
- Using tab-delimited format (will fail parsing)
- Temperature in °F when Material Profile is in °C
- Missing Node IDs (solver will halt)
- Exporting from FEA with 1-based indexing when modal stress uses 0-based (or vice versa)

#### 8.6.4 Advanced Tuning: Iteration Controls and Diagnostics

**Iteration Controls** (see Section 8.5.4):
- Adjust **Max Iterations** and **Tolerance** if convergence warnings appear
- A yellow warning label reminds you that relaxed settings may impact accuracy

**Plasticity Diagnostics Checkbox**:
- When enabled in Time History Mode, MARS overlays two additional curves on a secondary Y-axis:
  - **Δεₚ(t)**: Incremental plastic strain per time step (useful for identifying when yielding occurs)
  - **εₚ(t)**: Cumulative plastic strain (tracks total inelastic deformation)
- Useful for validating that plasticity correction activates at expected stress levels
- Helps debug non-convergence: if Δεₚ oscillates wildly, tighten tolerance or check material data

#### 8.6.5 Output Files

After solving with plasticity enabled, MARS exports:

- `corrected_von_mises.csv` — Plastically corrected peak von Mises stress per node  
- `plastic_strain.csv` — Equivalent plastic strain at peak  
- `time_of_max_corrected_von_mises.csv` — Time instant of corrected peak

In **Time History Mode**, the corrected history replaces the elastic history for plotting and export.

---

### 8.7 Interpreting Corrected Results

#### 8.7.1 Stress Reduction

Corrected stress \(\sigma_{\text{corr}} < \sigma_e\) reflects plasticity's stress-redistributing effect. Typical reductions:
- **5–15%** for low plastic strains (\(\varepsilon_p < 0.1\%\))  
- **20–40%** for moderate plasticity (\(\varepsilon_p \sim 1\%\))  
- **>50%** for gross yielding (rare in design-allowable structures)

If corrected stress remains above allowable limits, the notch may require redesign (radius increase, material upgrade).

#### 8.7.2 Plastic Strain as a Design Metric

Plastic strain indicates **local inelastic deformation**. Design thresholds:
- \(\varepsilon_p < 0.2\%\) — Elastic shakedown likely; low-cycle fatigue governs  
- \(0.2\% < \varepsilon_p < 2\%\) — Controlled plasticity; use strain-life methods  
- \(\varepsilon_p > 2\%\) — Ductile exhaustion or ratcheting risk; verify with nonlinear FEA

Combine plastic strain with rainflow-counted stress ranges for **strain-based fatigue** (Coffin-Manson, Morrow).

#### 8.7.3 Comparison with Elastic Results

Always compare:
- **Elastic von Mises** vs. **Corrected von Mises** to quantify notch effect  
- **Peak locations** (elastic vs. corrected) — plasticity may shift hot spots slightly  
- **Time of peak** — corrected peaks can occur at different instants due to history effects

Use side-by-side visualizations in the Display tab to assess impact.

---

### 8.8 Limitations and Assumptions

1. **Monotonic or proportional loading**: Neuber/Glinka assume stress components scale together. Nonproportional multiaxial paths reduce accuracy.  
2. **Notch-root approximation**: Methods model a **single material point**. Steep gradients or large plastic zones require full FEA.  
3. **Isotropic J₂ plasticity**: Anisotropy, kinematic hardening details, and Bauschinger effects are not captured.  
4. **No creep or rate effects**: Corrections are quasi-static. High-rate or creep-dominated scenarios need specialized models.  
5. **Temperature is instantaneous**: Each correction uses the *current* temperature; thermal history effects (microstructural changes) are ignored.  
6. **IBG experimental status**: Incremental method requires careful benchmarking—use Neuber/Glinka for production work until IBG is validated.

---

### 8.9 Verification Checklist for Plasticity Corrections

- [ ] Material hardening curves obtained from **cyclic tests** (not monotonic tensile data).  
- [ ] Temperature field corresponds to the **same load case** as the modal stresses.  
- [ ] Corrected stress **below elastic stress** (if not, check material data or convergence settings).  
- [ ] Plastic strains **reasonable** for the material (compare to handbook values for similar alloys/loadings).  
- [ ] Solver converged within iteration limit (watch Console messages for warnings).  
- [ ] For fatigue: corrected stress and plastic strain used consistently in damage calculations.  
- [ ] If using **Extrapolation Mode = Plateau**, confirm material exhibits limited hardening.  
- [ ] Cross-validate critical nodes with **detailed nonlinear FEA** for design-critical components.

---

### 8.10 Further Reading on Plasticity Correction Methods

- **Neuber, H.** (1961). "Theory of Stress Concentration for Shear-Strained Prismatical Bodies with Arbitrary Nonlinear Stress-Strain Law." *Journal of Applied Mechanics*.  
  *Original derivation of the K_σ K_ε = K_t² rule.*

- **Glinka, G.** (1985). "Energy Density Approach to Calculation of Inelastic Strain-Stress Near Notches and Cracks." *Engineering Fracture Mechanics*.  
  *Foundation of the energy-density method; widely used in automotive and aerospace.*

- **Buczynski, A. & Glinka, G.** (2003). "An Analysis of Elasto-Plastic Strains and Stresses in Notched Bodies Subjected to Cyclic Non-Proportional Loading Paths." *Proceedings ICF*.  
  *Incremental formulation for tensor histories; basis for the IBG implementation in MARS.*

- **Dowling, N.E.** (2013). *Mechanical Behavior of Materials*, 4th ed., Pearson.  
  *Chapter on notch analysis and local strain approaches; practical examples.*

- **SAE J1099** — Technical Report on Fatigue Under Complex Loading.  
  *Industry-standard guidance on combining notch corrections with fatigue counting.*

---

## 9. Interpreting MARS Outputs

### 9.1 Peak Values and Time Stamps

For each node, MARS reports the **maximum** value of a metric (e.g., `σ_vm,max`) and the **time of occurrence**. Use these to:

- Capture snapshots for visualization.  
- Cross-check against known loading events.  
- Compare with instrumentation data if available.

### 9.2 Time-History Plots

Time history mode lets you inspect nodal response vs. time:

- Identify resonance by locating sustained large amplitudes.  
- Evaluate damping by observing decay after excitation.  
- Export CSV to perform Fourier analysis or combine with fatigue tools.

### 9.3 Animation

Animations blend deformation with color-mapped stress. They help communicate mode participation and the spatial march of peak values. Keep deformation scaling reasonable (<5) to avoid misinterpretation.

---

## 10. Computational Precision and Performance

### 10.1 Floating-Point Precision

MARS offers two numerical precision modes (configurable via `Settings → Advanced`):

#### Single Precision (float32)
- **Significand**: ~7 decimal digits (24-bit mantissa)
- **Range**: ±1.2×10⁻³⁸ to ±3.4×10³⁸
- **Memory**: 4 bytes per value
- **Speed**: 2-4× faster than double on modern CPUs; GPU acceleration particularly effective
- **Suitable for**: Most engineering analyses where stress gradients are smooth and fatigue lives < 10⁶ cycles

#### Double Precision (float64)
- **Significand**: ~15 decimal digits (53-bit mantissa)
- **Range**: ±2.2×10⁻³⁰⁸ to ±1.8×10³⁰⁸
- **Memory**: 8 bytes per value
- **Speed**: Baseline (1×)
- **Suitable for**: Critical aerospace components, extreme stress concentrations, high-cycle fatigue (>10⁶), or validation against reference solutions

**Recommendation**: Start with single precision. Switch to double only if:
- Fatigue damage accumulation shows numerical noise
- Plasticity correction produces non-physical oscillations
- Results are sensitive to small changes in inputs

### 10.2 Memory Management

MARS dynamically allocates memory for matrix operations based on the **RAM Allocation %** setting (default 70%):

- Larger allocations enable processing of bigger datasets in single chunks, reducing I/O overhead
- Lower allocations leave more memory for concurrent applications
- The solver automatically falls back to chunked processing if a single allocation would exceed the limit

**Typical requirements** (double precision):
- 10,000 nodes × 100 modes × 1000 timesteps ≈ 8 GB
- 100,000 nodes × 200 modes × 5000 timesteps ≈ 800 GB (requires chunking)

### 10.3 GPU Acceleration

When enabled (requires NVIDIA CUDA):

- **Accelerated operations**: Dense matrix-matrix and matrix-vector multiplications (modal superposition)
- **Not accelerated**: File I/O, rainflow counting, VTK rendering
- **Speedup**: Typically 3-8× for models > 50,000 nodes; diminishing returns below 10,000 nodes
- **Precision**: Both float32 and float64 supported on modern GPUs (Compute Capability ≥6.0)

If CUDA is not detected, solver silently falls back to CPU with a console message.

---

## 11. Assumptions & Limitations

1. **Linearity**: Material and geometric nonlinearities are not captured (except via plasticity correction at notches).  
2. **Small Displacements**: Modal superposition relies on small strain theory.  
3. **Mode Orthogonality**: Requires correct mass normalization.  
4. **Proportional Damping**: Non-proportional damping would re-couple modes (rare in practice).  
5. **Data Fidelity**: Accuracy tied to quality of modal stresses and coordinates.  
6. **Numerical Precision**: Single-precision mode may accumulate roundoff error in extremely long time histories (>10⁶ timesteps).

---

## 12. Verification Checklist Before Reporting

- [ ] Modal set covers forcing bandwidth and has sufficient mass participation.  
- [ ] Peak displacements/stresses align with expectations from hand calculations or spot checks.  
- [ ] Fatigue parameters match material data sheets.  
- [ ] Animation and hotspot review performed for critical components.  
- [ ] Any steady-state stress file corresponds to the same load case and coordinate system.  
- [ ] Units double-checked (especially after unit conversions in FEA exports).
- [ ] Advanced Settings reviewed: appropriate precision and RAM allocation for problem size.

---

## 13. Further Study Resources

- **Textbooks**  
  - R.W. Clough & J. Penzien, *Dynamics of Structures* – foundational treatment of modal analysis.  
  - A.K. Chopra, *Dynamics of Structures* – practical engineering examples and damping discussions.  
  - S.S. Rao, *Mechanical Vibrations* – comprehensive coverage of modal truncation and participation factors.

- **Standards & Guides**  
  - ASTM E1049 – Rainflow counting method.  
  - ASME Boiler and Pressure Vessel Code, Section III Appendices – fatigue evaluation procedures.  
  - Eurocode 3 / AISC Design Guides – structural steel dynamic design.

---

## 14. Glossary

| Term | Definition |
| --- | --- |
| Modal coordinate `q_i(t)` | Time-dependent amplitude of mode `i`. |
| Mode shape `φ_i` | Displacement pattern associated with a natural frequency. |
| Natural frequency `ω_i` | Angular frequency of mode `i` (rad/s). |
| Damping ratio `ζ_i` | Fraction of critical damping for mode `i`. |
| Von Mises stress `σ_vm` | Scalar measure of distortion energy; used for ductile yield checks. |
| Principal stresses `s₁, s₂, s₃` | Eigenvalues of the stress tensor; `s₁` is maximum tension, `s₃` maximum compression. |
| Rainflow counting | Algorithm that collapses stress-time histories into cycles. |
| Miner's Rule | Linear fatigue damage accumulation method. |
| Plasticity correction | Notch-root approximation methods that reduce elastic stress to account for local yielding. |
| Neuber's Rule | Plasticity correction equating stress×strain product to elastic equivalent. |
| Glinka's Method | Energy-density-based plasticity correction; more conservative than Neuber. |
| IBG | Incremental Buczynski–Glinka method; tensor time-history plasticity correction (experimental). |
| Plastic strain `εₚ` | Permanent inelastic strain accumulated after yielding. |
| Hardening curve | Stress-strain relationship beyond yield; defines flow stress vs. plastic strain. |
| Equivalent stress | Scalar measure combining tensor components; von Mises is standard for ductile J₂ plasticity. |
| Temperature field | Spatial distribution of temperature used to adjust material properties node-by-node. |
| Single precision | Floating-point format with ~7 significant digits; faster but less accurate. |
| Double precision | Floating-point format with ~15 significant digits; slower but more accurate. |
| GPU acceleration | Use of NVIDIA CUDA for parallel matrix operations; requires compatible hardware. |
| RAM allocation | Percentage of system memory MARS is allowed to use for solver operations. |

---

### Closing Remark

Use MARS as a **modal microscope**: it reveals how each mode contributes to the physical response. With the theory in this manual, you can interpret that view, justify engineering decisions, and communicate structural dynamics behavior to colleagues and stakeholders with confidence.
