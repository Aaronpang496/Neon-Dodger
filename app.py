import random
import streamlit as st

st.set_page_config(
    page_title="Treasure Hunt",
    page_icon="💎",
    layout="centered",
)

SIZE = 5
GOAL = 3


def new_game():
    # The center tile is your safe starting point.
    positions = [i for i in range(SIZE * SIZE) if i != 12]
    random.shuffle(positions)

    board = ["🌿"] * (SIZE * SIZE)

    for position in positions[:5]:
        board[position] = "💎"

    for position in positions[5:10]:
        board[position] = "💣"

    for position in positions[10:13]:
        board[position] = "⚡"

    board[12] = "🏕️"

    st.session_state.game = {
        "board": board,
        "revealed": {12},
        "energy": 14,
        "gems": 0,
        "message": "Your adventure begins! Pick a mystery tile.",
        "finished": False,
        "won": False,
    }


if "game" not in st.session_state:
    new_game()

game = st.session_state.game


def explore(position):
    if game["finished"] or position in game["revealed"]:
        return

    game["revealed"].add(position)
    game["energy"] -= 1
    item = game["board"][position]

    if item == "💎":
        game["gems"] += 1
        game["message"] = "💎 You found a sparkling gem!"

    elif item == "💣":
        game["energy"] -= 2
        game["message"] = "💥 A trap! You lost 2 extra energy."

    elif item == "⚡":
        game["energy"] += 4
        game["message"] = "⚡ A magic spring! You gained 4 energy."

    else:
        game["message"] = random.choice([
            "🌿 Just grass. Very suspicious grass.",
            "🦎 A tiny lizard wishes you good luck.",
            "🪨 You found a rock. It believes in you.",
            "👀 Nothing here… keep searching!",
            "🐸 A frog says: 'The treasure is somewhere.'",
        ])

    game["energy"] = max(0, game["energy"])

    if game["gems"] >= GOAL:
        game["finished"] = True
        game["won"] = True
        game["message"] = "🏆 You found the treasure! Adventure complete."

    elif game["energy"] <= 0:
        game["finished"] = True
        game["message"] = "🌙 Out of energy! Your explorer needs a nap."


st.title("💎 Treasure Hunt")
st.write(
    "**Find 3 gems before your energy runs out.** "
    "Tap any mystery tile to explore it."
)

left, right = st.columns(2)
left.metric("⚡ Energy", game["energy"])
right.metric("💎 Gems", f"{game['gems']} / {GOAL}")

st.progress(min(game["gems"] / GOAL, 1.0))

if game["finished"]:
    if game["won"]:
        st.success(game["message"])
    else:
        st.error(game["message"])
else:
    st.info(game["message"])

for row in range(SIZE):
    columns = st.columns(SIZE)

    for column in range(SIZE):
        position = row * SIZE + column
        revealed = position in game["revealed"]

        label = (
            game["board"][position]
            if revealed or game["finished"]
            else "❓"
        )

        with columns[column]:
            if st.button(
                label,
                key=f"tile_{position}",
                use_container_width=True,
                disabled=revealed or game["finished"],
            ):
                explore(position)
                st.rerun()

st.caption(
    "Every exploration costs 1 energy. "
    "💎 Gem · 💣 Trap: −2 extra energy · ⚡ Spring: +4 energy"
)

if game["finished"]:
    if game["won"] and not st.session_state.get("celebrated", False):
        st.balloons()
        st.session_state.celebrated = True

    st.write("The full island is revealed above. Try a new island!")

if st.button("🏝️ New island", type="primary"):
    new_game()
    st.session_state.celebrated = False
    st.rerun()
