import json
import uuid

import graphviz
import streamlit as st

st.set_page_config(
    page_title="My Mind Map",
    page_icon="🧠",
    layout="wide",
)

COLORS = {
    "Purple": "#7c3aed",
    "Blue": "#2563eb",
    "Green": "#059669",
    "Orange": "#c2410c",
    "Pink": "#be185d",
    "Dark": "#334155",
}


def blank_map():
    return {
        "root": {
            "text": "Central Topic",
            "parent": None,
            "color": "Purple",
        }
    }


if "topics" not in st.session_state:
    st.session_state.topics = blank_map()

topics = st.session_state.topics


def descendants(topic_id):
    found = {topic_id}
    pending = [topic_id]

    while pending:
        parent = pending.pop()
        for key, value in topics.items():
            if value["parent"] == parent and key not in found:
                found.add(key)
                pending.append(key)

    return found


def validate_map(data):
    if not isinstance(data, dict) or not 1 <= len(data) <= 500:
        raise ValueError("A map must have between 1 and 500 topics.")

    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ValueError("Invalid topic format.")

        if not isinstance(value.get("text"), str):
            raise ValueError("Every topic needs text.")

        if len(value["text"]) > 120:
            raise ValueError("Topic text must be 120 characters or fewer.")

        if value.get("color") not in COLORS:
            raise ValueError("Invalid topic color.")

        parent = value.get("parent")
        if parent is not None and parent not in data:
            raise ValueError("A topic has a missing parent.")

    roots = [key for key, value in data.items()
             if value.get("parent") is None]

    if len(roots) != 1:
        raise ValueError("The map needs exactly one central topic.")

    for key in data:
        visited = set()
        current = key

        while current is not None:
            if current in visited:
                raise ValueError("Circular branches are not supported.")
            visited.add(current)
            current = data[current].get("parent")

    return data


st.title("🧠 My Mind Map")
st.caption(
    "Write your own topics and branches. "
    "No AI or API key required."
)

st.subheader("1. Choose a topic")

topic_ids = list(topics)

selected = st.selectbox(
    "Topic to edit or add branches to",
    options=topic_ids,
    format_func=lambda key: (
        f"{topics[key]['text'] or 'Untitled'} "
        f"· {topic_ids.index(key) + 1}"
    ),
)

topic = topics[selected]

with st.form(f"edit_{selected}"):
    text = st.text_input(
        "Topic text",
        value=topic["text"],
        max_chars=120,
    )

    color = st.selectbox(
        "Topic color",
        options=list(COLORS),
        index=list(COLORS).index(topic["color"]),
    )

    if st.form_submit_button("Save changes"):
        topics[selected]["text"] = text.strip() or "Untitled"
        topics[selected]["color"] = color
        st.rerun()

st.subheader("2. Add a branch")

with st.form(f"add_{selected}", clear_on_submit=True):
    new_text = st.text_input(
        "New subtopic",
        placeholder="Write a branch here",
        max_chars=120,
    )

    if st.form_submit_button("＋ Add subtopic"):
        if not new_text.strip():
            st.warning("Write a topic first.")
        elif len(topics) >= 500:
            st.warning("This app supports up to 500 topics.")
        else:
            new_id = uuid.uuid4().hex
            topics[new_id] = {
                "text": new_text.strip(),
                "parent": selected,
                "color": topic["color"],
            }
            st.rerun()

if topic["parent"] is not None:
    with st.expander("Delete selected topic"):
        to_remove = descendants(selected)
        st.warning(
            f"This deletes the selected topic and its subtopics: "
            f"{len(to_remove)} topic(s)."
        )

        if st.button(
            "Confirm deletion",
            key=f"delete_{selected}",
        ):
            for key in to_remove:
                del topics[key]
            st.rerun()

st.subheader("3. Your map")

direction = st.radio(
    "Map direction",
    ["Left to right", "Top to bottom"],
    horizontal=True,
)

graph = graphviz.Digraph()

graph.attr(
    rankdir="LR" if direction == "Left to right" else "TB",
    bgcolor="transparent",
    nodesep="0.4",
    ranksep="0.7",
)

graph.attr(
    "node",
    shape="box",
    style="rounded,filled",
    fontname="Arial",
    fontcolor="white",
    margin="0.18,0.12",
)

for key, value in topics.items():
    graph.node(
        key,
        label=graphviz.escape(value["text"]),
        fillcolor=COLORS[value["color"]],
        color="#111827" if key == selected else COLORS[value["color"]],
        penwidth="3" if key == selected else "1",
    )

for key, value in topics.items():
    if value["parent"] is not None:
        graph.edge(
            value["parent"],
            key,
            color=COLORS[value["color"]],
            arrowhead="none",
            penwidth="2",
        )

st.graphviz_chart(graph, use_container_width=True)

st.caption(
    "Choose topics using the dropdown above. "
    "The boxes in this diagram are not editing buttons."
)

st.subheader("4. Save or open a map")

st.download_button(
    "⬇ Download map",
    data=json.dumps(topics, ensure_ascii=False, indent=2),
    file_name="mind-map.json",
    mime="application/json",
)

uploaded = st.file_uploader(
    "Open a saved map",
    type=["json"],
)

if uploaded is not None:
    if st.button("Load this file"):
        try:
            if uploaded.size > 2_000_000:
                raise ValueError("Choose a file smaller than 2 MB.")

            loaded = validate_map(json.loads(uploaded.getvalue()))
            st.session_state.topics = loaded
            st.rerun()
        except (ValueError, TypeError, KeyError) as error:
            st.error(f"Could not open this map: {error}")

with st.expander("Start over"):
    st.warning("Download your current map before replacing it.")

    if st.button("Create a blank map"):
        st.session_state.topics = blank_map()
        st.rerun()

st.info(
    "Your map stays in the current Streamlit session, "
    "but it is not permanently stored. "
    "Download your map before closing or refreshing."
)
