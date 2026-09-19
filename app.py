import base64
import html
import json
import random
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import streamlit as st
from sampler import AdaptiveSampler
from analysis import estimate_line
from report import render_report

st.set_page_config(page_title="MAL Threshold Test", layout="centered")
RESULTS_DIR = Path("results")
ASSETS = Path("assets")
BURN_IN = 40
REFIT_EVERY = 10
BUTTONS = [("BAD", "MAUVAIS"), ("MID", "MID"), ("GOOD", "BON"), ("IDK", "PTDR T KI")]
UVC_FROM, UVC_CHANCE = 20, 0.10
CELEBRATE_AT = 3
MEME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
              ".gif": "image/gif", ".webp": "image/webp"}

@st.cache_data
def load_pool():
    with open("pool.json", encoding="utf-8") as f:
        pool = json.load(f)
    counts = Counter(a["title"] for a in pool)
    for a in pool:
        if counts[a["title"]] > 1 and a["year"]:
            a["title"] = f'{a["title"]} ({a["year"]})'
    return pool

@st.cache_data
def load_memes():
    folder = ASSETS / "memes"
    if not folder.exists():
        return []
    return [f"data:{MEME_TYPES[p.suffix.lower()]};base64,"
            f"{base64.b64encode(p.read_bytes()).decode()}"
            for p in sorted(folder.iterdir()) if p.suffix.lower() in MEME_TYPES]

if "phase" not in st.session_state:
    st.session_state.phase = "setup"

def valid_count():
    return sum(1 for r in st.session_state.responses if r["label"] != "IDK")

def roll_uvc():
    if valid_count() >= UVC_FROM and random.random() < UVC_CHANCE:
        st.session_state.uvc = set(range(4)) if random.random() < 0.5 else {random.randrange(4)}
    else:
        st.session_state.uvc = set()

def save():
    RESULTS_DIR.mkdir(exist_ok=True)
    data = {"username": st.session_state.username, "target": st.session_state.target,
            "started": st.session_state.started, "responses": st.session_state.responses}
    st.session_state.save_path.write_text(json.dumps(data, indent=1), encoding="utf-8")

def start():
    name = re.sub(r"[^A-Za-z0-9_-]", "", st.session_state.username_input) or "anonymous"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.username = name
    st.session_state.target = st.session_state.target_input
    st.session_state.started = stamp
    st.session_state.save_path = RESULTS_DIR / f"{name}_{stamp}.json"
    st.session_state.sampler = AdaptiveSampler(load_pool())
    st.session_state.current = st.session_state.sampler.next()
    st.session_state.responses = []
    st.session_state.shown_at = time.time()
    st.session_state.uvc = set()
    st.session_state.celebrate = False
    st.session_state.phase = "rating"

def load_past():
    data = json.loads(st.session_state.past_file.read_text(encoding="utf-8"))
    st.session_state.responses = data["responses"]
    st.session_state.phase = "done"

def record(label):
    a = st.session_state.current
    sampler = st.session_state.sampler
    st.session_state.responses.append({
        "id": a["id"], "title": a["title"], "score": a["score"],
        "members": a["members"], "label": label,
        "seconds": round(time.time() - st.session_state.shown_at, 2),
        "focus": sampler.focus,
    })
    save()
    n_valid = valid_count()
    if label != "IDK" and n_valid == CELEBRATE_AT:
        st.session_state.celebrate = True
    if label != "IDK" and n_valid >= BURN_IN and (n_valid - BURN_IN) % REFIT_EVERY == 0:
        est = estimate_line(st.session_state.responses)
        if est is not None:
            sampler.set_focus(est)
    st.session_state.current = sampler.next()
    st.session_state.shown_at = time.time()
    roll_uvc()
    if n_valid >= st.session_state.target or st.session_state.current is None:
        st.session_state.phase = "done"

def celebrate():
    memes = load_memes()
    rng = random.Random()
    tags = []
    picks = []
    while memes and len(picks) < 14:
        batch = memes[:]
        rng.shuffle(batch)
        picks += batch
    for i, src in enumerate(picks[:14]):
        tags.append(
            f'<img src="{src}" class="meme" style="left:{rng.randint(0, 80)}vw;'
            f' top:{rng.randint(0, 75)}vh; width:{rng.randint(12, 24)}vw;'
            f' rotate:{rng.randint(-25, 25)}deg; animation-delay:{i * 0.12:.2f}s;">')
    st.markdown("""
    <style>
    .meme { position:fixed; z-index:9999; pointer-events:none; opacity:0;
            animation: pop 6s ease-out forwards; }
    @keyframes pop { 0% {opacity:0; scale:0.3} 8% {opacity:1; scale:1.15}
                     12% {scale:1} 80% {opacity:1} 100% {opacity:0} }
    </style>""" + "".join(tags), unsafe_allow_html=True)
    sound = ASSETS / "67.mp3"
    if sound.exists():
        st.audio(sound.read_bytes(), format="audio/mpeg", autoplay=True)
        

CARD = """
<div style="text-align:center;">
  <div style="height:420px; display:flex; align-items:center; justify-content:center;">
    {img}
  </div>
  <div style="height:3.2em; margin-top:12px; font-size:1.3em; font-weight:600;
              line-height:1.6em; overflow:hidden;">{title}</div>
</div>
"""

if st.session_state.get("celebrate"):
    st.session_state.celebrate = False
    celebrate()

phase = st.session_state.phase

if phase == "setup":
    st.title("Is 7.75 the line?")
    st.text_input("Username (optional)", key="username_input")
    st.number_input("Number of ratings", min_value=30, max_value=200,
                    value=150, step=10, key="target_input")
    st.caption("150 is recommended. Fewer ratings make an inconclusive verdict "
               "more likely, and past 200 the pool runs short of high scoring anime. "
               "IDK answers don't count toward the total.")
    st.button("Start", on_click=start, type="primary")

    files = sorted(RESULTS_DIR.glob("*.json"), reverse=True) if RESULTS_DIR.exists() else []
    if files:
        st.divider()
        st.selectbox("Or view a past session", files, format_func=lambda p: p.stem,
                     key="past_file")
        st.button("View report", on_click=load_past)

elif phase == "rating":
    a = st.session_state.current
    img = (f'<img src="{a["image"]}" style="max-height:420px; max-width:100%; '
           f'object-fit:contain; border-radius:8px;">' if a["image"] else "No image")
    st.markdown(CARD.format(img=img, title=html.escape(a["title"])),
                unsafe_allow_html=True)
    _, middle, _ = st.columns([1, 3, 1])
    with middle:
        cols = st.columns(4)
        for i, (col, (label, text)) in enumerate(zip(cols, BUTTONS)):
            shown = "UVC" if i in st.session_state.uvc else text
            col.button(shown, key=f"btn_{label}", on_click=record, args=(label,),
                       width="stretch")
    st.markdown(f"<p style='text-align:center; opacity:0.6;'>"
                f"{valid_count()} / {st.session_state.target}</p>",
                unsafe_allow_html=True)

else:
    render_report(st.session_state.responses)
    st.divider()
    st.button("Start a new session",
              on_click=lambda: st.session_state.update(phase="setup"))
