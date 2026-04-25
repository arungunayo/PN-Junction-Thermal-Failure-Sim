import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# --Page config
st.set_page_config(
    page_title="PN Junction – Thermal Failure Sim",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --Constants------------------------------------------------------------------------
Eg0   = 1.17          # Silicon band gap at 0 K (eV)
alpha = 4.73e-4       # Varshni coefficient (eV/K)
beta  = 636           # Varshni coefficient (K)
kB    = 8.617e-5      # Boltzmann constant (eV/K)
ni300 = 1.5e10        # Intrinsic carrier concentration at 300 K (cm-3)
T300  = 300.0

# -- Physics functions ---------------------------------------------------------------
def band_gap(T):
    return Eg0 - (alpha * T**2) / (T + beta)

def ni(T):
    Eg_T   = band_gap(T)
    Eg_300 = band_gap(T300)
    return ni300 * (T / T300)**1.5 * np.exp(-Eg_T / (2*kB*T) + Eg_300 / (2*kB*T300))

def failure_temp(Na):
    T_range = np.linspace(200, 1000, 5000)
    ni_vals  = ni(T_range)
    idx = np.argmin(np.abs(ni_vals - Na))
    return T_range[idx]

# -- Sidebar controls --------------------------------------------------------------
with st.sidebar:
    st.title("Parameters")

    T_current = st.slider(
        "Temperature (K)",
        min_value=200, max_value=800, value=300, step=5,
        help="Drag to change the operating temperature of the junction."
    )

    st.markdown("---")
    st.markdown("**Doping concentration Nₐ (cm⁻³)**")
    Na_exp = st.slider(
        "log₁₀(Nₐ)",
        min_value=13.0, max_value=18.0, value=16.0, step=0.5,
        format="%.1f"
    )
    Na = 10**Na_exp

    st.markdown("---")
    st.markdown(
        """
        **How to understand this:**
        - The junction works as a diode while **nᵢ ≪ Nₐ**
        - When **nᵢ → Nₐ**, intrinsic carriers overwhelm doping
        - The I-V asymmetry collapses — the diode **fails thermally**
        """
    )

# -- Derived values ----------------------------------------------------------------
T       = float(T_current)
ni_now  = ni(T)
Eg_now  = band_gap(T)
kT_now  = kB * T
T_fail  = failure_temp(Na)
ratio   = ni_now / Na          # 0 → safe, → 1 → failing

# --Status label -----------------------------------------------------------------
if ratio < 0.01:
    status, status_color = "Diode functioning normally", "green"
elif ratio < 0.1:
    status, status_color = "⚠️ Thermal degradation beginning", "orange"
elif ratio < 0.5:
    status, status_color = "🔴 Significant thermal leakage", "red"
else:
    status, status_color = "Junction has lost rectification", "red"

# -- Metric cards ---------------------------------------------------------------
st.markdown("## PN Junction — Thermal Failure Simulation")
st.markdown(f"**Junction status:** :{status_color}[{status}]")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Temperature",         f"{T:.0f} K")
c2.metric("Band gap Eₘ",        f"{Eg_now:.3f} eV",
          delta=f"{Eg_now - band_gap(300):.3f} eV vs 300K")
c3.metric("nᵢ / Nₐ ratio",     f"{ratio:.2e}",
          help="Approaches 1 as the junction fails")
c4.metric("Thermal failure at",  f"{T_fail:.0f} K",
          help="Temperature where nᵢ ≈ Nₐ for current doping")

st.markdown("---")

# -- Build T-axis arrays ----------------------------------------------------------
T_arr    = np.linspace(200, 800, 600)
ni_arr   = ni(T_arr)
Eg_arr   = band_gap(T_arr)
ratio_arr = ni_arr / Na

# Color the curve by temperature (blue → red)
def t_color(T_val):
    t = (T_val - 200) / 600
    r = int(30  + t * 210)
    g = int(100 - t * 80)
    b = int(220 - t * 190)
    return f"rgb({r},{g},{b})"

# --Plots-------------------------------------------------------------------------
fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        "Intrinsic carrier concentration nᵢ vs Temperature",
        "nᵢ / Nₐ ratio — how close to failure"
    ),
    horizontal_spacing=0.12,
)

# --Plot 1: nᵢ vs T ---------------------------------------------------------------
# Full curve (faded)
fig.add_trace(go.Scatter(
    x=T_arr, y=ni_arr,
    mode="lines",
    line=dict(color="rgba(150,150,200,0.25)", width=2),
    showlegend=False,
    hovertemplate="T=%{x:.0f}K<br>nᵢ=%{y:.2e} cm⁻³<extra></extra>",
), row=1, col=1)

# Colored segment up to current T
mask = T_arr <= T
fig.add_trace(go.Scatter(
    x=T_arr[mask], y=ni_arr[mask],
    mode="lines",
    line=dict(color=t_color(T), width=3),
    name="nᵢ (T ≤ current)",
    hovertemplate="T=%{x:.0f}K<br>nᵢ=%{y:.2e} cm⁻³<extra></extra>",
), row=1, col=1)

# Doping line
fig.add_hline(
    y=Na, line_dash="dash", line_color="tomato", line_width=1.5,
    annotation_text=f"Nₐ = {Na:.1e} cm⁻³",
    annotation_position="bottom right",
    row=1, col=1,
)

# Current point
fig.add_trace(go.Scatter(
    x=[T], y=[ni_now],
    mode="markers",
    marker=dict(size=12, color=t_color(T), line=dict(color="white", width=2)),
    name=f"T = {T:.0f} K",
    hovertemplate=f"T={T:.0f}K<br>nᵢ={ni_now:.2e} cm⁻³<extra></extra>",
), row=1, col=1)

# Failure temperature line
if 200 <= T_fail <= 800:
    fig.add_vline(
        x=T_fail, line_dash="dot", line_color="tomato", line_width=1.5,
        annotation_text=f"Fail ≈ {T_fail:.0f}K",
        annotation_position="top right",
        row=1, col=1,
    )

fig.update_yaxes(type="log", title_text="nᵢ (cm⁻³)", row=1, col=1)
fig.update_xaxes(title_text="Temperature (K)", row=1, col=1)

# --Plot 2: ratio ni/Na vs T---------------------------------------------------
# Background danger zones
fig.add_hrect(y0=0,    y1=0.01,  fillcolor="rgba(0,200,100,0.08)",  line_width=0, row=1, col=2)
fig.add_hrect(y0=0.01, y1=0.1,   fillcolor="rgba(255,200,0,0.08)",  line_width=0, row=1, col=2)
fig.add_hrect(y0=0.1,  y1=0.5,   fillcolor="rgba(255,100,0,0.10)",  line_width=0, row=1, col=2)
fig.add_hrect(y0=0.5,  y1=10,    fillcolor="rgba(200,0,0,0.12)",    line_width=0, row=1, col=2)

fig.add_trace(go.Scatter(
    x=T_arr, y=ratio_arr,
    mode="lines",
    line=dict(color="rgba(150,150,200,0.25)", width=2),
    showlegend=False,
    hovertemplate="T=%{x:.0f}K<br>nᵢ/Nₐ=%{y:.3f}<extra></extra>",
), row=1, col=2)

mask2 = T_arr <= T
fig.add_trace(go.Scatter(
    x=T_arr[mask2], y=ratio_arr[mask2],
    mode="lines",
    line=dict(color=t_color(T), width=3),
    name="nᵢ/Nₐ ratio",
    hovertemplate="T=%{x:.0f}K<br>nᵢ/Nₐ=%{y:.3f}<extra></extra>",
), row=1, col=2)

fig.add_hline(
    y=1.0, line_dash="dash", line_color="tomato", line_width=1.5,
    annotation_text="nᵢ = Nₐ (failure threshold)",
    annotation_position="bottom right",
    row=1, col=2,
)

fig.add_trace(go.Scatter(
    x=[T], y=[ratio],
    mode="markers",
    marker=dict(size=12, color=t_color(T), line=dict(color="white", width=2)),
    showlegend=False,
    hovertemplate=f"T={T:.0f}K<br>nᵢ/Nₐ={ratio:.3f}<extra></extra>",
), row=1, col=2)

fig.update_yaxes(type="log", title_text="nᵢ / Nₐ", row=1, col=2)
fig.update_xaxes(title_text="Temperature (K)", row=1, col=2)

fig.update_layout(
    height=450,
    margin=dict(t=50, b=40, l=60, r=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(size=13),
)
fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")

st.plotly_chart(fig, use_container_width=True)

# -- Band gap sub-plot -----------------------------------------------
with st.expander("Band gap Eₘ vs Temperature"):
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=T_arr, y=Eg_arr,
        mode="lines",
        line=dict(color="rgba(100,160,220,0.4)", width=2),
        showlegend=False,
    ))
    fig2.add_trace(go.Scatter(
        x=T_arr[T_arr <= T], y=Eg_arr[T_arr <= T],
        mode="lines",
        line=dict(color=t_color(T), width=3),
        name="Eₘ(T)",
    ))
    fig2.add_trace(go.Scatter(
        x=[T], y=[Eg_now],
        mode="markers",
        marker=dict(size=11, color=t_color(T), line=dict(color="white", width=2)),
        showlegend=False,
    ))
    fig2.update_layout(
        height=280,
        xaxis_title="Temperature (K)",
        yaxis_title="Band gap (eV)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=40),
    )
    fig2.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    fig2.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    st.plotly_chart(fig2, use_container_width=True)

# ── Physics summary ────────────────────────────────────────────────────────────
with st.expander(" Equations used"):
    st.markdown(r"""
**Varshni equation (band gap):**
$$E_g(T) = E_g(0) - \frac{\alpha T^2}{T + \beta}$$
- $E_g(0) = 1.17\ \text{eV}$, $\alpha = 4.73 \times 10^{-4}\ \text{eV/K}$, $\beta = 636\ \text{K}$

**Intrinsic carrier concentration:**
$$n_i(T) = n_i(300)\cdot\left(\frac{T}{300}\right)^{3/2} \cdot \exp\!\left(-\frac{E_g(T)}{2k_BT} + \frac{E_g(300)}{2k_B \cdot 300}\right)$$

**Thermal failure condition:**
$$n_i(T) \approx N_a \implies \text{junction loses rectification}$$
""")