import numpy as np
import plotly.graph_objects as go
import statsmodels.api as sm
import streamlit as st
from sklearn.metrics import roc_curve, roc_auc_score
from analysis import to_frame, fit_threshold, bootstrap_threshold, verdict, CLAIM

COLORS = {"SUPPORTED": "#2e9e5b", "REFUTED": "#d64545",
          "INCONCLUSIVE": "#d9a13b", "NO RELATIONSHIP": "#888888"}
LABEL_COLORS = {"BAD": "#d64545", "MID": "#d9a13b", "GOOD": "#2e9e5b"}

@st.cache_data(show_spinner="Crunching the numbers...")
def analyze(responses):
    df = to_frame(responses)
    if len(df) < 10 or df["y"].nunique() < 2:
        return None
    try:
        model, s_star = fit_threshold(df)
    except Exception:
        return None
    _, _, est = bootstrap_threshold(df, n_boot=2000, seed=0)
    word, sentence = verdict(model, est)
    b0, b1 = model.params["const"], model.params["score"]

    fpr, tpr, thr = roc_curve(df["y"], df["score"])
    j = int(np.argmax(tpr - fpr))
    pos, neg = df[df["y"] == 1], df[df["y"] == 0]

    df["log_members"] = np.log10(df["members"])
    try:
        m2 = sm.Logit(df["y"], sm.add_constant(df[["score", "log_members"]])).fit(disp=0)
        b2, p2 = float(m2.params["log_members"]), float(m2.pvalues["log_members"])
    except Exception:
        b2 = p2 = None

    return {
        "df": df, "word": word, "sentence": sentence, "b0": b0, "b1": b1,
        "s_star": s_star, "ci": np.percentile(est, [2.5, 97.5]),
        "fuzz": 1 / b1 if b1 > 0 else float("inf"),
        "fpr": fpr, "tpr": tpr, "auc": roc_auc_score(df["y"], df["score"]),
        "youden": float(thr[j]) if np.isfinite(thr[j]) else None,
        "youden_pt": (fpr[j], tpr[j]),
        "claim_pt": ((neg["score"] >= CLAIM).mean(), (pos["score"] >= CLAIM).mean()),
        "b2": b2, "p2": p2,
    }

def render_report(responses):
    r = analyze(responses)
    if r is None:
        st.warning("Not enough usable ratings to analyze. You need at least 10, "
                   "with both GOOD and non GOOD answers.")
        return
    df, lo, hi = r["df"], *r["ci"]

    st.markdown(f"""
    <div style="text-align:center; padding:24px 0;">
      <div style="font-size:3.2em; font-weight:800; color:{COLORS[r['word']]};">{r['word']}</div>
      <div style="font-size:1.1em; opacity:0.8; margin-bottom:18px;">{r['sentence']}</div>
      <div style="font-size:2em; font-weight:700;">Your line: {r['s_star']:.2f}</div>
      <div style="opacity:0.7;">95% range {lo:.2f} to {hi:.2f} · sharpness ±{r['fuzz']:.2f}
      · {len(df)} ratings</div>
    </div>""", unsafe_allow_html=True)
    if r["word"] == "INCONCLUSIVE" and r["fuzz"] > 0.5:
        st.caption("Your verdicts are blurry near your line, so the rule behaves "
                   "more like a vibe than a sharp cutoff.")

    st.divider()
    st.subheader("Your curve")
    st.caption("Each dot is one rating, placed at the anime's MAL score. The curve is "
               "the fitted chance you say GOOD. The shaded band is where your line "
               "plausibly sits, the dashed line is the claim.")
    x = np.linspace(df["score"].min() - 0.3, df["score"].max() + 0.3, 200)
    fig = go.Figure()
    fig.add_vrect(x0=lo, x1=hi, fillcolor="#888", opacity=0.15, line_width=0)
    fig.add_trace(go.Scatter(x=x, y=1 / (1 + np.exp(-(r["b0"] + r["b1"] * x))),
                             mode="lines", name="P(GOOD)", line=dict(width=3)))
    jitter = np.random.default_rng(0).uniform(-0.04, 0.04, len(df))
    for label, color in LABEL_COLORS.items():
        sub = df["label"] == label
        fig.add_trace(go.Scatter(
            x=df.loc[sub, "score"], y=df.loc[sub, "y"] + jitter[sub.to_numpy()],
            mode="markers", name=label, marker=dict(color=color, size=8),
            text=df.loc[sub, "title"], hovertemplate="%{text}<br>%{x}<extra></extra>"))
    fig.add_vline(x=CLAIM, line_dash="dash")
    fig.add_vline(x=r["s_star"])
    fig.update_layout(xaxis_title="MAL score", yaxis_title="Chance of GOOD", height=420)
    st.plotly_chart(fig)

    st.subheader("How well MAL predicts you")
    st.caption(f"AUC {r['auc']:.2f}: the chance that a random anime you called GOOD "
               f"has a higher MAL score than a random one you didn't. 0.5 is a coin "
               f"flip, 1.0 is perfect.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=r["fpr"], y=r["tpr"], mode="lines", name="ROC",
                             line=dict(width=3)))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Coin flip",
                             line=dict(dash="dot", color="#888")))
    fig.add_trace(go.Scatter(x=[r["claim_pt"][0]], y=[r["claim_pt"][1]], mode="markers",
                             name=f"Cutoff {CLAIM}", marker=dict(size=14, symbol="x")))
    if r["youden"] is not None:
        fig.add_trace(go.Scatter(x=[r["youden_pt"][0]], y=[r["youden_pt"][1]],
                                 mode="markers", name=f"Best cutoff {r['youden']:.2f}",
                                 marker=dict(size=14)))
    fig.update_layout(xaxis_title="False positive rate", yaxis_title="True positive rate",
                      height=420)
    st.plotly_chart(fig)

    st.subheader("Does popularity sway you?")
    if r["b2"] is None:
        st.write("Couldn't fit the popularity model on this data.")
    else:
        odds = np.exp(r["b2"])
        if r["p2"] < 0.05:
            direction = "more" if r["b2"] > 0 else "less"
            st.write(f"Yes. At the same MAL score, an anime with 10 times more members "
                     f"makes you {odds:.1f}x {'as' if odds >= 1 else ''} likely in odds "
                     f"to call it GOOD, so you're {direction} generous with popular shows.")
        else:
            st.write(f"No clear effect (p = {r['p2']:.2f}). Once the MAL score is "
                     f"accounted for, popularity doesn't noticeably change your verdicts.")
    fig = go.Figure()
    for label, color in LABEL_COLORS.items():
        sub = df[df["label"] == label]
        fig.add_trace(go.Scatter(x=sub["score"], y=sub["members"], mode="markers",
                                 name=label, marker=dict(color=color, size=8),
                                 text=sub["title"],
                                 hovertemplate="%{text}<br>%{x}<extra></extra>"))
    fig.update_layout(xaxis_title="MAL score", yaxis_title="Members", yaxis_type="log",
                      height=420)
    st.plotly_chart(fig)
