import pandas as pd
import statsmodels.api as sm
import warnings
import numpy as np

CLAIM = 7.75

def verdict(model, estimates, claim=CLAIM, tol=0.2):
    b1 = model.params["score"]
    if b1 <= 0 or model.pvalues["score"] > 0.05:
        return "NO RELATIONSHIP", "Your ratings don't follow MAL scores closely enough to find a line."
    lo90, hi90 = np.percentile(estimates, [5, 95])
    lo95, hi95 = np.percentile(estimates, [2.5, 97.5])
    if claim - tol <= lo90 and hi90 <= claim + tol:
        return "SUPPORTED", f"Your line sits within {tol} of {claim}."
    if hi95 < claim:
        return "REFUTED", f"Your line is clearly below {claim}."
    if lo95 > claim:
        return "REFUTED", f"Your line is clearly above {claim}."
    return "INCONCLUSIVE", "The data can't tell yet. More ratings would narrow it down."

def bootstrap_threshold(df, n_boot=2000, seed=None):
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(n_boot):
        sample = df.sample(len(df), replace=True, random_state=rng)
        if sample["y"].nunique() < 2:
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _, s = fit_threshold(sample)
        except Exception:
            continue
        if np.isfinite(s):
            estimates.append(s)
    estimates = np.array(estimates)
    low, high = np.percentile(estimates, [2.5, 97.5])
    return low, high, estimates

def to_frame(responses):
    df = pd.DataFrame(responses)
    df = df[df["label"] != "IDK"].copy()
    df["y"] = (df["label"] == "GOOD").astype(int)
    return df

def fit_threshold(df):
    X = sm.add_constant(df["score"])
    model = sm.Logit(df["y"], X).fit(disp=0)
    b0, b1 = model.params["const"], model.params["score"]
    return model, -b0 / b1


def estimate_line(responses):
    df = to_frame(responses)
    if df["y"].nunique() < 2:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, s = fit_threshold(df)
    except Exception:
        return None
    return float(np.clip(s, 5.0, 9.25)) if np.isfinite(s) else None
