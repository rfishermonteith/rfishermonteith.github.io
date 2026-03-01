import numpy as np
import pandas as pd
from scipy.stats import beta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.gaussian_process import GaussianProcessClassifier, GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
import plotly.express as px

# --------------------- DATA ---------------------
data = [
(70, False),
(80, True),
(70, True),
(75, False),
(80, False),
(95, False),
(95, True),
(60, False),
(50, True),
(50, True),
(70, True),
(95, True),
(80, True),
(70, True),
(60, False),
(70, True),
(50, True),
(50, True),
(90, True),
(80, True),
(50, False),
]

df = pd.DataFrame(data, columns=["confidence","in_band"])
df["in_band"] = df["in_band"].astype(int)
df["confidence"] = df["confidence"]/100

grouped = df.groupby("confidence").agg(successes=("in_band","sum"),
                                       n=("in_band","count")).reset_index()
grouped = grouped.sort_values("confidence", ascending=False)

grouped["means"] = grouped["successes"]/grouped["n"]

# Raw data
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=df["confidence"], y=df["in_band"], mode="markers", name="Raw booleans"))
# fig.add_trace(go.Scatter(x=grouped["confidence"], y=grouped["means"], mode="markers", name="Means"))
# fig.update_layout(
#     xaxis={"title":{"text":"Prediction confidence level"},"tickformat": ".0%"},
#     yaxis={"title":{"text":"Prediction outcome"}}
# )

fig = px.strip(df, x="confidence",y="in_band")
fig.add_trace(go.Scatter(x=grouped["confidence"], y=grouped["means"], mode="markers", name="Means", marker_symbol="x"))

fig.update_layout(
    xaxis={"title":{"text":"Prediction confidence level"},"tickformat": ".0%"},
    yaxis={"title":{"text":"Prediction outcome"}}

)
fig.update_traces(marker=dict(size=8,

                              ),
                  # selector=dict(mode='markers')
                  )

# fig.show()
j = fig.to_json()
with open("../../assets/viz/kernel-smoothing/chart_1.json", "w") as f:
    f.write(j)


# Uniform prior
grouped["a_post"] = grouped["successes"] + 1
grouped["b_post"] = grouped["n"] - grouped["successes"] + 1

# Ridgeline plot
from plotly.colors import n_colors
colors = px.colors.qualitative.Pastel
# colors = n_colors('rgb(5, 200, 200)', 'rgb(200, 10, 10)', grouped.shape[0], colortype='rgb')
p_grid = np.linspace(1e-4, 1-1e-4, 800)

fig = go.Figure()
for i, row in enumerate(grouped.itertuples()):
    conf = row.confidence
    a = row.a_post
    b = row.b_post

    pdf = beta.pdf(p_grid, a, b)
    cap = np.percentile(pdf, 99.5)
    pdf = np.clip(pdf, 0, cap)

    # width = (pdf / pdf.max()) * 0.9 * 3
    width = pdf * 0.9 * 3 / 100

    y_up = p_grid
    x_right = conf+width

    x_right_bottom = conf
    x_left_bottom = conf

    x_poly = np.concatenate([
        [x_right_bottom],
        x_right,
        [x_left_bottom]
    ])

    y_poly = np.concatenate([
        [0.0],
        y_up,
        [1.0]
    ])

    # 90% credible interval (drawn as two horizontal segments)
    lower = beta.ppf(0.05, a, b) * 1
    upper = beta.ppf(0.95, a, b) * 1


    fig.add_trace(
        go.Scatter(
            x=x_poly,
            y=y_poly,
            mode="lines",
            fill="toself",
            line=dict(color="black", width=1),
            fillcolor=colors[i % len(colors)],
            opacity=0.8,
            name=f"{conf:.0%} (k={row.successes}, n={row.n})",
            showlegend=False
        ),
        # row=1, col=1
    )

fig.update_layout(
    xaxis={"title":{"text":"Prediction confidence level"},"tickformat": ".0%"},
    yaxis={"title":{"text":"Probability of true confidence"}, "tickformat": ".0%"}
)
# fig.show()

j = fig.to_json()
with open("../../assets/viz/kernel-smoothing/chart_2.json", "w") as f:
    f.write(j)




# ---------------- Kernel + Bayesian Smoothing ----------------
fig = go.Figure()
bandwidths = np.logspace(-2, 0, 24).round(3)
# bandwidths = [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.1, 0.5, 1]
for bandwidth in bandwidths:
    x = df["confidence"].values.astype(float)
    y = df["in_band"].values.astype(float)
    # bandwidth = 0.01
    grid = np.arange(0.5, 1.0001, 0.01)

    def rbf_weights(x_eval, x, h):
        return np.exp(-0.5 * ((x[:,None] - x_eval[None,:]) / h) ** 2)

    W = rbf_weights(grid, x, bandwidth)

    def kernel_regression(W, y):
        num = (W.T * y).sum(axis=1)
        den = W.sum(axis=0)
        return num / den

    mean_kernel = kernel_regression(W, y)

    # Bootstrap CI
    B = 2000
    boot = []
    rng = np.random.default_rng(1)
    for _ in range(B):
        idx = rng.integers(0, len(x), size=len(x))
        xb = x[idx]; yb = y[idx]
        Wb = rbf_weights(grid, xb, bandwidth)
        boot.append(kernel_regression(Wb, yb))
    boot = np.array(boot)
    lower_kernel = np.nanpercentile(boot, 5, axis=0)
    upper_kernel = np.nanpercentile(boot, 95, axis=0)


    fig.add_trace(go.Scatter(visible=False, x=grid, y=mean_kernel,
                             name=f"Kernel mean",
                             line=dict(color="blue")),
                  # row=2, col=1
                  )

    fig.add_trace(go.Scatter(visible=False,x=grid, y=upper_kernel,
                             line=dict(width=0),
                             showlegend=False),
                  # row=2, col=1
                  )

    fig.add_trace(go.Scatter(visible=False,x=grid, y=lower_kernel,
                             fill="tonexty",
                             name="90% bootstrap CI",
                             line=dict(width=0),
                             fillcolor="rgba(0,0,255,0.15)"),
                  # row=2, col=1
                  )

fig.update_layout(
    xaxis={"title":{"text":"Prediction confidence level"},"tickformat": ".0%", "range":[0.5,1]},
    yaxis={"title":{"text":"Probability of true confidence"}, "tickformat": ".0%", "range": [0,1]}
)
starting = 8
# Make 8th trace visible
for i in range(starting*3,starting*3+3):
    fig.data[i].visible = True

# Create and add slider
steps = []
for i in range(len(bandwidths)):
    step = dict(
        method="update",
        args=[{"visible": [False] * len(fig.data)},
              {"title": "Slider switched to step: " + str(bandwidths[i])}],  # layout attribute
        label=f"{bandwidths[i]}"
    )
    step["args"][0]["visible"][i*3:(i+1)*3] = 3*[True]  # Toggle i'th trace to "visible"
    steps.append(step)

sliders = [dict(
    active=starting,
    currentvalue={"prefix": "bandwidth: "},
    pad={"t": 50},
    steps=steps
)]

fig.update_layout(
    sliders=sliders
)

fig.show()

j = fig.to_json()
with open("../../assets/viz/kernel-smoothing/chart_3.json", "w") as f:
    f.write(j)


# Kernelised Beta-Binomial
tau0 = 2.0
weighted_successes = (W.T * y).sum(axis=1)
weighted_trials = W.sum(axis=0)
m0 = grid / 100.0
a0 = m0 * tau0
b0 = (1 - m0) * tau0
a_post = a0 + weighted_successes
b_post = b0 + (weighted_trials - weighted_successes)
beta_mean = a_post / (a_post + b_post)
beta_lower = beta.ppf(0.05, a_post, b_post)
beta_upper = beta.ppf(0.95, a_post, b_post)

# Gaussian Process
kernel = 1.0 * RBF(length_scale=10.0, length_scale_bounds="fixed")
gp = GaussianProcessClassifier(kernel=kernel, optimizer=None)
gp.fit(x.reshape(-1,1), y)
gp_probs = gp.predict_proba(grid.reshape(-1,1))[:,1]

# --------------------- PLOTLY LAYOUT ---------------------
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.1,
    row_heights=[0.45, 0.275, 0.275],
    subplot_titles=[
        "Posterior p Distributions per Confidence Level (Jeffreys Beta-Binomial)",
        "Kernel Regression Calibration Smoother",
        "Kernel Beta-Binomial + Gaussian Process Calibration"
    ]
)

# ---------- PANEL 1: Joy Plot ----------
p_grid = np.linspace(1e-4, 1-1e-4, 800)
colors = ["rgba(100,149,237,0.45)",
          "rgba(255,165,0,0.45)",
          "rgba(34,139,34,0.45)",
          "rgba(148,0,211,0.45)",
          "rgba(220,20,60,0.45)",
          "rgba(128,128,128,0.45)",
          "rgba(255,105,180,0.45)"]

for i, row in enumerate(grouped.itertuples()):
    conf = int(row.confidence)
    a = row.a_post
    b = row.b_post

    pdf = beta.pdf(p_grid, a, b)
    cap = np.percentile(pdf, 99)
    pdf = np.clip(pdf, 0, cap)

    width = (pdf / pdf.max()) * 0.9 * 3
    y_up = p_grid * 100

    # ⭐ LEFT boundary of ridge (curved)
    x_left = conf - width

    # ⭐ Explicit vertical right boundary
    x_right_top = conf
    x_right_bottom = conf

    # ⭐ Build polygon in clockwise order:
    # left edge up → right top → right bottom → close at left bottom
    x_poly = np.concatenate([
        x_left,                    # left curved boundary up
        [x_right_top, x_right_bottom, x_left[0]]
    ])

    y_poly = np.concatenate([
        y_up,                      # same y positions
        [y_up[-1], y_up[0], y_up[0]]
    ])

    fig.add_trace(
        go.Scatter(
            x=x_poly,
            y=y_poly,
            mode="lines",
            fill="toself",
            line=dict(color="black", width=1),
            fillcolor=colors[i % len(colors)],
            name=f"{conf}% (k={row.successes}, n={row.n})",
            showlegend=False
        ),
        row=1, col=1
    )

    # 90% credible interval (drawn as two horizontal segments)
    lower = beta.ppf(0.05, a, b) * 100
    upper = beta.ppf(0.95, a, b) * 100

    fig.add_trace(
        go.Scatter(
            x=[conf, conf + 2.5],
            y=[lower, lower],
            mode="lines",
            line=dict(color="red"),
            showlegend=False
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=[conf, conf + 2.5],
            y=[upper, upper],
            mode="lines",
            line=dict(color="red"),
            showlegend=False
        ),
        row=1, col=1
    )

# ---------------- PANEL 2: Kernel smoother ----------------
fig.add_trace(go.Scatter(x=grid, y=mean_kernel*100,
                         name="Kernel mean (h=6)",
                         line=dict(color="blue")),
              row=2, col=1)

fig.add_trace(go.Scatter(x=grid, y=upper_kernel*100,
                         line=dict(width=0),
                         showlegend=False),
              row=2, col=1)

fig.add_trace(go.Scatter(x=grid, y=lower_kernel*100,
                         fill="tonexty",
                         name="90% bootstrap CI",
                         line=dict(width=0),
                         fillcolor="rgba(0,0,255,0.15)"),
              row=2, col=1)

# ---------------- PANEL 3: Kernel Beta–Binomial + GP ----------------
fig.add_trace(go.Scatter(x=grid, y=beta_mean*100,
                         name="Kernel Beta-binomial mean",
                         line=dict(color="blue")),
              row=3, col=1)

fig.add_trace(go.Scatter(x=grid, y=beta_upper*100,
                         line=dict(width=0),
                         showlegend=False),
              row=3, col=1)

fig.add_trace(go.Scatter(x=grid, y=beta_lower*100,
                         fill="tonexty",
                         name="90% credible interval",
                         line=dict(width=0),
                         fillcolor="rgba(0,0,255,0.15)"),
              row=3, col=1)

fig.add_trace(go.Scatter(x=grid, y=gp_probs*100,
                         name="GP mean",
                         line=dict(color="orange", dash="dash")),
              row=3, col=1)

fig.add_trace(go.Scatter(x=grid, y=grid,
                         name="Ideal diagonal",
                         line=dict(color="gray", dash="dot")),
              row=3, col=1)

# ---------------- AXES / LABELS ----------------
fig.update_xaxes(range=[50, 100], title="Confidence (%)", row=3, col=1)

for r in [1, 2, 3]:
    fig.update_yaxes(range=[0, 100], ticksuffix="%", title="Probability", row=r, col=1)

fig.update_layout(
    height=1000,
    width=950,
    title="Combined Calibration Visualization — Plotly Interactive"
)

fig.show()

j = fig.to_json()

with open("../../assets/viz/kernel-smoothing/chart2.json", "w") as f:
    f.write(j)

# --------------------- KERNEL REGRESSION + LINEAR PRIOR (TWO SLIDERS) ---------------------
# Prior strength blends between kernel regression (w=0) and the diagonal y=x (w=1).
# At w=0 this is identical to chart_3.
#
# Uses method="skip" on slider steps so that a custom JS event handler
# (in _includes/plotly-dual-slider.html) can read both slider positions
# and set the correct visibility.

fig_lp = go.Figure()
bandwidths_lp = np.logspace(-2, 0, 12).round(3)
prior_strengths = np.array([0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0])

default_bw_idx = 4
default_prior_idx = 0  # no prior by default

n_bw = len(bandwidths_lp)
n_prior = len(prior_strengths)

for bw in bandwidths_lp:
    W_lp = rbf_weights(grid, x, bw)
    mean_k = kernel_regression(W_lp, y)

    # Bootstrap CI
    boot_lp = []
    rng_lp = np.random.default_rng(1)
    for _ in range(2000):
        idx = rng_lp.integers(0, len(x), size=len(x))
        Wb = rbf_weights(grid, x[idx], bw)
        boot_lp.append(kernel_regression(Wb, y[idx]))
    boot_lp = np.array(boot_lp)
    lower_k = np.nanpercentile(boot_lp, 5, axis=0)
    upper_k = np.nanpercentile(boot_lp, 95, axis=0)

    for ps in prior_strengths:
        blended_mean = (1 - ps) * mean_k + ps * grid
        blended_upper = (1 - ps) * upper_k + ps * grid
        blended_lower = (1 - ps) * lower_k + ps * grid

        fig_lp.add_trace(go.Scatter(
            visible=False, x=grid, y=blended_mean,
            name="Blended mean", line=dict(color="blue")))
        fig_lp.add_trace(go.Scatter(
            visible=False, x=grid, y=blended_upper,
            line=dict(width=0), showlegend=False))
        fig_lp.add_trace(go.Scatter(
            visible=False, x=grid, y=blended_lower,
            fill="tonexty", name="90% bootstrap CI",
            line=dict(width=0), fillcolor="rgba(0,0,255,0.15)"))

# Always-visible traces: diagonal + observed means
n_combo_traces = n_bw * n_prior * 3
fig_lp.add_trace(go.Scatter(
    x=grid, y=grid, name="Ideal diagonal (prior)",
    line=dict(color="gray", dash="dot")))
fig_lp.add_trace(go.Scatter(
    x=grouped["confidence"], y=grouped["means"], mode="markers",
    name="Observed means", marker=dict(size=8, color="red", symbol="x")))

# Set default visible
default_idx = (default_bw_idx * n_prior + default_prior_idx) * 3
for k in range(3):
    fig_lp.data[default_idx + k].visible = True

# Bandwidth slider — method="skip" so JS handler controls visibility
bw_steps = []
for i in range(n_bw):
    bw_steps.append(dict(method="skip", args=[{}, {}], label=f"{bandwidths_lp[i]}"))

# Prior strength slider — method="skip" so JS handler controls visibility
prior_steps = []
for j in range(n_prior):
    prior_steps.append(dict(method="skip", args=[{}, {}], label=f"{prior_strengths[j]}"))

fig_lp.update_layout(
    sliders=[
        dict(active=default_bw_idx, currentvalue={"prefix": "bandwidth: "},
             pad={"t": 50}, steps=bw_steps),
        dict(active=default_prior_idx, currentvalue={"prefix": "prior strength: "},
             pad={"t": 100}, steps=prior_steps),
    ],
    xaxis={"title": {"text": "Prediction confidence level"}, "tickformat": ".0%", "range": [0.5, 1]},
    yaxis={"title": {"text": "Estimated true probability"}, "tickformat": ".0%", "range": [0, 1]},
    title="Kernel Regression with Linear Prior (y = x)"
)

fig_lp.show()

j = fig_lp.to_json()
with open("../../assets/viz/kernel-smoothing/chart_4.json", "w") as f:
    f.write(j)
