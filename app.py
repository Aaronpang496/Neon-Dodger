from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Neon Assault",
    page_icon="🚀",
    layout="centered",
)

st.title("🚀 Neon Assault")
st.caption(
    "Drag to fly. Fire automatically. "
    "Destroy enemies, collect upgrades, and dash through danger."
)

html = Path(__file__).with_name("game.html").read_text(
    encoding="utf-8"
)

components.html(html, height=900, scrolling=True)
