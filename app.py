"""AI-Driven Game Review Compiler – Streamlit application entry point."""

import os
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from src.image_handler import create_image_collage, download_image, load_user_image
from src.review_generator import generate_review
from src.steam_fetcher import extract_game_info, get_game_details, search_game

load_dotenv()

st.set_page_config(
    page_title="AI Game Review Compiler",
    page_icon="🎮",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input(
        "OpenAI API Key",
        value=os.environ.get("OPENAI_API_KEY", ""),
        type="password",
        help="Enter your OpenAI API key to generate reviews.",
    )
    st.markdown("---")
    st.markdown(
        "**About:** Fetches game data from Steam and uses OpenAI GPT-4o to generate "
        "detailed, personalised game reviews."
    )
    st.markdown(
        "Built for **MATH-395 – Creating AI in the Loop** · "
        "[Steam Store](https://store.steampowered.com)"
    )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🎮 AI-Driven Game Review Compiler")
st.markdown(
    "Search for a game on Steam, optionally share your own experience and screenshots, "
    "then let AI compile a comprehensive review."
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Step 1 & 2 – Find a game and collect user input
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("🔍 Step 1 – Find a Game on Steam")
    search_query = st.text_input(
        "Search by game title",
        placeholder="e.g. Hollow Knight, Elden Ring, Stardew Valley",
    )

    if search_query:
        with st.spinner("Searching Steam…"):
            try:
                results = search_game(search_query)
            except Exception as exc:
                st.error(f"Steam search failed: {exc}")
                results = []

        if results:
            game_options = {
                f"{r['name']} (App ID: {r['id']})": r["id"]
                for r in results[:10]
            }
            selected_label = st.selectbox("Select a game:", list(game_options.keys()))
            selected_app_id = game_options[selected_label]

            if st.button("Fetch Game Details", use_container_width=True):
                with st.spinner("Fetching game details from Steam…"):
                    try:
                        raw_data = get_game_details(selected_app_id)
                        if raw_data:
                            st.session_state["game_info"] = extract_game_info(raw_data)
                            st.success(
                                f"✅ Loaded: **{st.session_state['game_info']['name']}**"
                            )
                        else:
                            st.error(
                                "Could not load details for this game. "
                                "Please try another title."
                            )
                    except Exception as exc:
                        st.error(f"Failed to fetch game details: {exc}")
        else:
            st.warning("No results found – try a different search term.")

with col_right:
    st.subheader("✍️ Step 2 – Your Experience (optional)")
    user_experience = st.text_area(
        "Describe your personal gameplay experience",
        placeholder=(
            "e.g. I played for 60 hours and loved the boss fights, "
            "but found the early game slow…"
        ),
        height=160,
    )

    st.markdown("**📸 Your Screenshots (optional)**")
    uploaded_files = st.file_uploader(
        "Upload screenshots from your playthrough",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        help="Up to 4 images – these will appear alongside Steam screenshots in the review.",
    )

# ---------------------------------------------------------------------------
# Game info card
# ---------------------------------------------------------------------------
if "game_info" in st.session_state:
    gi = st.session_state["game_info"]
    st.markdown("---")
    st.subheader(f"🎮 {gi['name']}")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Developer", gi.get("developer") or "—")
        st.metric("Genre", ", ".join(gi.get("genres", [])[:2]) or "—")
    with m2:
        st.metric("Publisher", gi.get("publisher") or "—")
        st.metric("Release Date", gi.get("release_date") or "—")
    with m3:
        st.metric("Price", gi.get("price") or "Free")
        if gi.get("metacritic_score") is not None:
            st.metric("Metacritic", gi["metacritic_score"])

    if gi.get("short_description"):
        st.markdown(gi["short_description"])

    if gi.get("header_image"):
        st.image(gi["header_image"], use_container_width=True)

# ---------------------------------------------------------------------------
# Generate review
# ---------------------------------------------------------------------------
st.markdown("---")
if st.button("🚀 Generate Review", type="primary", use_container_width=True):
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif "game_info" not in st.session_state:
        st.error("Please search for a game and click **Fetch Game Details** first.")
    else:
        gi = st.session_state["game_info"]

        with st.spinner("Generating AI-powered review – this may take a few seconds…"):
            try:
                client = OpenAI(api_key=api_key)
                review_text = generate_review(
                    gi, user_experience=user_experience or None, client=client
                )
            except Exception as exc:
                st.error(f"Review generation failed: {exc}")
                review_text = None

        if review_text:
            # Collect images
            all_images = []
            with st.spinner("Fetching screenshots…"):
                for url in gi.get("screenshot_urls", [])[:3]:
                    img = download_image(url)
                    if img:
                        all_images.append(img)

            for uploaded in uploaded_files or []:
                img = load_user_image(uploaded)
                if img:
                    all_images.append(img)

            # ---- Display ----
            st.markdown("---")
            st.header(f"📝 Review: {gi['name']}")

            if gi.get("header_image"):
                header_img = download_image(gi["header_image"])
                if header_img:
                    buf = BytesIO()
                    header_img.save(buf, format="PNG")
                    st.image(buf.getvalue(), use_container_width=True)

            st.markdown(review_text)

            if all_images:
                st.subheader("📸 Screenshots")
                collage = create_image_collage(all_images, max_images=4)
                if collage:
                    buf = BytesIO()
                    collage.save(buf, format="PNG")
                    st.image(
                        buf.getvalue(),
                        use_container_width=True,
                        caption="Game Screenshots",
                    )

            # Download button
            full_review = f"# {gi['name']} – Game Review\n\n{review_text}"
            st.download_button(
                label="⬇️ Download Review (Markdown)",
                data=full_review,
                file_name=f"{gi['name'].replace(' ', '_')}_review.md",
                mime="text/markdown",
            )
