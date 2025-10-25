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

## 8. Interpreting MARS Outputs

### 8.1 Peak Values and Time Stamps

For each node, MARS reports the **maximum** value of a metric (e.g., `σ_vm,max`) and the **time of occurrence**. Use these to:

- Capture snapshots for visualization.  
- Cross-check against known loading events.  
- Compare with instrumentation data if available.

### 8.2 Time-History Plots

Time history mode lets you inspect nodal response vs. time:

- Identify resonance by locating sustained large amplitudes.  
- Evaluate damping by observing decay after excitation.  
- Export CSV to perform Fourier analysis or combine with fatigue tools.

### 8.3 Animation

Animations blend deformation with color-mapped stress. They help communicate mode participation and the spatial march of peak values. Keep deformation scaling reasonable (<5) to avoid misinterpretation.

---

## 9. Assumptions & Limitations

1. **Linearity**: Material and geometric nonlinearities are not captured.  
2. **Small Displacements**: Modal superposition counts on small strain theory.  
3. **Mode Orthogonality**: Requires correct mass normalization.  
4. **Proportional Damping**: Non-proportional damping would re-couple modes (rare in practice).  
5. **Data Fidelity**: Accuracy tied to quality of modal stresses and coordinates.

---

## 10. Verification Checklist Before Reporting

- [ ] Modal set covers forcing bandwidth and has sufficient mass participation.  
- [ ] Peak displacements/stresses align with expectations from hand calculations or spot checks.  
- [ ] Fatigue parameters match material data sheets.  
- [ ] Animation and hotspot review performed for critical components.  
- [ ] Any steady-state stress file corresponds to the same load case and coordinate system.  
- [ ] Units double-checked (especially after unit conversions in FEA exports).

---

## 11. Further Study Resources

- **Textbooks**  
  - R.W. Clough & J. Penzien, *Dynamics of Structures* – foundational treatment of modal analysis.  
  - A.K. Chopra, *Dynamics of Structures* – practical engineering examples and damping discussions.  
  - S.S. Rao, *Mechanical Vibrations* – comprehensive coverage of modal truncation and participation factors.

- **Standards & Guides**  
  - ASTM E1049 – Rainflow counting method.  
  - ASME Boiler and Pressure Vessel Code, Section III Appendices – fatigue evaluation procedures.  
  - Eurocode 3 / AISC Design Guides – structural steel dynamic design.

---

## 12. Glossary

| Term | Definition |
| --- | --- |
| Modal coordinate `q_i(t)` | Time-dependent amplitude of mode `i`. |
| Mode shape `φ_i` | Displacement pattern associated with a natural frequency. |
| Natural frequency `ω_i` | Angular frequency of mode `i` (rad/s). |
| Damping ratio `ζ_i` | Fraction of critical damping for mode `i`. |
| Von Mises stress `σ_vm` | Scalar measure of distortion energy; used for ductile yield checks. |
| Principal stresses `s₁, s₂, s₃` | Eigenvalues of the stress tensor; `s₁` is maximum tension, `s₃` maximum compression. |
| Rainflow counting | Algorithm that collapses stress-time histories into cycles. |
| Miner’s Rule | Linear fatigue damage accumulation method. |

---

### Closing Remark

Use MARS as a **modal microscope**: it reveals how each mode contributes to the physical response. With the theory in this manual, you can interpret that view, justify engineering decisions, and communicate structural dynamics behavior to colleagues and stakeholders with confidence.
