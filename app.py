"""Streamlit web interface for the Game Review workflow.

This app provides a web UI for generating AI-powered reviews of Steam games.
It wraps the LangGraph workflow, adding real-time progress display via streaming.
"""

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

from ai_in_loop.config import Config
from ai_in_loop.graph import build_graph
from ai_in_loop.state import GameState
from ai_in_loop.tools import build_review_pdf

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(page_title="Video Game Review Content Generator", page_icon="🎮", layout="wide")

# ── Custom CSS Styling ───────────────────────────────────────────────
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@700&display=swap');

        /* Main app background */
        .main {
            background: #000000;
            background-attachment: fixed;
            color: #0A0A0A;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
            position: relative;
        }
        
        /* Overall page background */
        body, .stApp {
            background: #000000;
            background-color: #000000 !important;
            background-attachment: fixed;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
        }

        .stApp {
            position: relative;
            isolation: isolate;
            overflow-x: hidden;
        }

        .stApp > * {
            position: relative;
            z-index: 1;
        }
        
        /* All text elements */
        * {
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: #000000;
        }
        
        /* Main title with enhanced glow */
        h1 {
            color: #F0F3F8;
            text-shadow: 0 0 20px rgba(20, 75, 176, 0.3),
                         0 0 40px rgba(20, 75, 176, 0.2),
                         0 0 60px rgba(240, 243, 248, 0.1);
            padding: 12px 0 8px 0;
            margin: 0 0 8px 0;
            border-bottom: none;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
            text-align: center;
            position: relative;
        }

        .arc-title {
            margin: -8px 0 10px 0 !important;
            text-align: center !important;
            font-family: 'Caveat', 'Brush Script MT', 'Segoe Script', cursive !important;
            font-size: 108px !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            line-height: 1 !important;
            color: #F0F3F8 !important;
            text-shadow: 0 0 12px rgba(20, 75, 176, 0.55),
                         0 0 28px rgba(20, 75, 176, 0.45),
                         0 0 44px rgba(240, 243, 248, 0.25) !important;
        }

        .title-logo {
            display: flex;
            justify-content: center;
            margin: 4px 0 10px 0;
        }

        .title-divider {
            width: 100%;
            height: 1px;
            background: #144BB0;
            margin: 10px 0 24px 0;
        }

        @media (max-width: 768px) {
            .arc-title {
                font-size: 72px !important;
            }
        }
        
        /* Subheadings */
        h2 {
            color: #F0F3F8;
            margin-top: 20px;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
        }
        
        /* Section headers */
        h3 {
            color: #F0F3F8;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
        }
        
        /* Input fields */
        input, textarea, select {
            background-color: #0A0A0A !important;
            color: #F3F6E9 !important;
            border: 1px solid transparent !important;
            border-radius: 8px !important;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace !important;
        }

        /* Keep border only for URL input and experience text area */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            border: 1px solid #144BB5 !important;
        }

        /* Force Streamlit dropdown/select borders */
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within {
            background-color: #0A0A0A !important;
            color: #F3F6E9 !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
        }

        /* Remove border only for age-check and rating dropdown controls */
        [data-testid="stSelectbox"]:has(input[aria-label="Day"]) div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"]:has(input[aria-label="Month"]) div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"]:has(input[aria-label="Year"]) div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"]:has(input[aria-label="Drop_Down"]) div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"]:has(input[aria-label="Day"]) div[data-baseweb="select"] > div:hover,
        [data-testid="stSelectbox"]:has(input[aria-label="Month"]) div[data-baseweb="select"] > div:hover,
        [data-testid="stSelectbox"]:has(input[aria-label="Year"]) div[data-baseweb="select"] > div:hover,
        [data-testid="stSelectbox"]:has(input[aria-label="Drop_Down"]) div[data-baseweb="select"] > div:hover,
        [data-testid="stSelectbox"]:has(input[aria-label="Day"]) div[data-baseweb="select"] > div:focus-within,
        [data-testid="stSelectbox"]:has(input[aria-label="Month"]) div[data-baseweb="select"] > div:focus-within,
        [data-testid="stSelectbox"]:has(input[aria-label="Year"]) div[data-baseweb="select"] > div:focus-within,
        [data-testid="stSelectbox"]:has(input[aria-label="Drop_Down"]) div[data-baseweb="select"] > div:focus-within {
            border-color: transparent !important;
            box-shadow: none !important;
        }

        [data-testid="stSelectbox"] div[data-baseweb="popover"],
        [data-testid="stMultiSelect"] div[data-baseweb="popover"],
        div[role="listbox"] {
            background-color: #0A0A0A !important;
            border: 1px solid transparent !important;
        }

        div[role="option"] {
            background-color: #0A0A0A !important;
            color: #F3F6E9 !important;
        }

        div[role="option"][aria-selected="true"],
        div[role="option"]:hover {
            background-color: #144BB5 !important;
            color: #F3F6E9 !important;
        }

        /* Make Streamlit's top bar match page background */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {
            background: #000000 !important;
        }
        
        input:focus, textarea:focus, select:focus {
            border-color: transparent !important;
            box-shadow: none !important;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: #144BB5 !important;
            box-shadow: 0 0 10px rgba(20, 75, 176, 0.3) !important;
        }
        
        /* Buttons with enhanced glow */
        button {
    background: linear-gradient(135deg, #003153  0%, #144BB5 50%, #2D709C 100%) !important;
    color: #F3F6E9 !important;
    border: 1px solid #003153 !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    font-weight: bold !important;
    text-transform: uppercase !important;
    position: relative !important;
    isolation: isolate !important;
    overflow: hidden !important;
    transition: transform 0.4s ease, box-shadow 0.4s ease !important;

    box-shadow: 
        0 4px 8px rgba(20, 75, 176, 0.3),
        0 0 20px rgba(20, 75, 176, 0.4);
}

        button::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: linear-gradient(135deg, #144BB7 0%, #144BB0 50%, #01847F 100%);
            opacity: 0;
            transition: opacity 0.45s ease;
            pointer-events: none;
            z-index: 0;
        }

        button,
        button span,
        button p,
        button div,
        [data-testid="stFileUploader"] button small {
            color: #F3F6E9 !important;
        }

        button span,
        button p,
        button div,
        [data-testid="stFileUploader"] button small {
            position: relative;
            z-index: 1;
        }
        
        button:hover {
            box-shadow: 0 8px 15px rgba(20, 75, 176, 0.4),
                        0 0 30px rgba(20, 75, 176, 0.3),
                        0 0 50px rgba(240, 243, 248, 0.1) !important;
            transform: translateY(-2px) !important;
        }

        button:hover::before {
            opacity: 1;
        }
        
        /* Expander/Dropdown */
        [data-testid="stExpander"] {
            border: 1px solid #144BB5 !important;
            border-radius: 10px;
            background-color: #0A0A0A;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
        }
        
        /* Metrics */
        [data-testid="metric-container"] {
            background-color: #0A0A0A;
            border: 1px solid #144BB5 !important;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace;
        }
        
        /* Status messages */
        .stWarning, .stError, .stSuccess {
            border-radius: 10px !important;
            border: 1px solid #144BB0 !important;
            padding: 15px !important;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace !important;
        }
        
        .stWarning {
            background-color: #3d2817 !important;
            border-color: #ff9500 !important;
        }
        
        .stError {
            background-color: #2d1117 !important;
            border-color: #00ff00 !important;
        }
        
        .stSuccess {
            background-color: #0d3b1a !important;
            border-color: #00d084 !important;
        }
        
        /* Info/Status box */
        [data-testid="stStatusContainer"] {
            background-color: #1a1a2e !important;
            border: 1px solid #144BB0 !important;
            border-radius: 10px !important;
            font-family: 'Consolas', 'Monaco', 'Menlo', 'DejaVu Sans Mono', monospace !important;
        }
        
        /* Divider */
        hr {
            border-color: #144BB0;
            margin: 30px 0;
        }
        
        .main::before,
        .main::after {
            content: none;
        }
        
        /* Add decorative light elements */
        .light-decoration {
            position: relative;
        }
        
        .light-decoration::before {
            content: '✨';
            position: absolute;
            top: -10px;
            right: -10px;
            font-size: 16px;
            opacity: 0.8;
            animation: twinkle 2s ease-in-out infinite;
        }
        
        @keyframes twinkle {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }
    </style>
""", unsafe_allow_html=True)

# ── Header with logo and title ────────────────────────────────────────
st.markdown('<div style="margin-top:-80px;"></div>', unsafe_allow_html=True)
logo_left, logo_mid, logo_right = st.columns([4, 1, 4])
with logo_mid:
    st.image("arclight.png", width=880)
st.markdown('<h1 class="arc-title">A.R.C</h1>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

# ── Session state for review history ─────────────────────────────────
if "review_history" not in st.session_state:
    st.session_state.review_history = []  # list of {"title": ..., "review": ..., "images": ...}
if "age_verified" not in st.session_state:
    st.session_state.age_verified = False
if "user_birthdate" not in st.session_state:
    st.session_state.user_birthdate = None
if "verified_url" not in st.session_state:
    st.session_state.verified_url = ""
if "selected_fullsize_image" not in st.session_state:
    st.session_state.selected_fullsize_image = None
if "selected_history_index" not in st.session_state:
    st.session_state.selected_history_index = None


# ── Cached graph + helper ────────────────────────────────────────────
# @st.cache_resource is like st.session_state but shared across all
# browser tabs and only runs the function once. It's the recommended
# way to cache expensive objects like compiled graphs or DB connections.
@st.cache_resource
def get_pipeline():
    """Build and cache the LangGraph workflow (runs once per session)."""
    cfg = Config.from_env()
    return build_graph(cfg)


def get_initial_state(
    url: str,
    user_exp: str | None,
    review_rating: str | None,
    user_images: list[str] | None,
    user_birthdate: tuple[int, str, int] | None,
) -> GameState:
    """Create the initial workflow state from user inputs."""
    return {
        "game_url": url,
        "identifier": None,
        "game_title": None,
        "developer": None,
        "publisher": None,
        "release_date": None,
        "official_description": None,
        "steam_rating": None,
        "hardware_requirement": None,
        "user_exp": user_exp,
        "review_rating": review_rating,
        "user_images": user_images,
        "user_birthdate": user_birthdate,
        "review": None,
        "warnings": [],
    }


def render_review_with_media(review: str, media_items: list[object] | None = None) -> None:
    """Render review paragraphs with one media item inserted after each paragraph."""
    paragraphs = review.split("\n\n") if review else []
    media_items = media_items or []
    media_index = 0

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        st.markdown(
            f"<p style='font-size: 25px; font-weight: bold; line-height: 1.6;'>{paragraph}</p>",
            unsafe_allow_html=True,
        )

        if media_index >= len(media_items):
            continue

        media = media_items[media_index]
        if isinstance(media, dict):
            media = media.get("value")

        if isinstance(media, str) and media.endswith((".webm", ".mp4")):
            st.video(media)
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(media, width=750)

        media_index += 1



# Human-readable labels for each workflow node
NODE_LABELS = {
    "parse_input": "Parsing Steam URL...",
    "fetch_game_info": "Fetching game info from Steam...",
    "prepare_official": "Preparing official description...",
    "merge_exp": "Merging player experience...",
    "merge_image": "Processing user images...",
    "merge_both": "Merging experience and images...",
    "summarize": "Generating review...",
}


# ── Two-column layout ────────────────────────────────────────────────
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("STEAM WEBPAGE URL")
    url = st.text_input(
        "Enter:",
        placeholder="https://store.steampowered.com/app/1234567/GameName/",
        label_visibility="visible",
    )

    # Age verification check
    if url != st.session_state.verified_url:
        st.session_state.age_verified = False
        st.session_state.user_birthdate = None
        st.session_state.verified_url = ""

    if url and "store.steampowered.com" in url:
        try:
            quick_check = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if quick_check.status_code == 200 and "birth date" in quick_check.text.lower():
                st.warning("This game requires age verification. Please enter your birth date to proceed.")
                col1, col2, col3 = st.columns(3)
                with col1:
                    day = st.selectbox("Day", list(range(1, 32)), key="day")
                with col2:
                    month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], key="month")
                with col3:
                    year = st.selectbox("Year", list(range(1900, 2026)), key="year")
                if st.button("Verify Age"):
                    st.session_state.age_verified = True
                    st.session_state.user_birthdate = (day, month, year)
                    st.session_state.verified_url = url
                    st.success("Age verified! You can now generate the review.")
        except:
            pass  # Ignore errors in quick check

    st.subheader("YOUR RATING")
    review_rating = st.selectbox(
        "Drop_Down",
        options=["", "1/10", "2/10", "3/10", "4/10", "5/10",
                 "6/10", "7/10", "8/10", "9/10", "10/10"],
        label_visibility="collapsed",
    )

    st.subheader("YOUR EXPERIENCE WITH THIS VIDEO GAME")
    user_exp = st.text_area("Text:", height=150, label_visibility="collapsed")

    st.subheader("UPLOAD YOUR SCREENSHOT!")
    uploaded_files = st.file_uploader(
        "Upload a file",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg"],
    )

    if uploaded_files:
        st.markdown("#### UPLOADED IMAGE PREVIEW")
        st.image(uploaded_files, caption=[f.name for f in uploaded_files], width=200)

    _, btn_col, _ = st.columns([1, 3, 1])
    with btn_col:
        analyze_button = st.button("Generate Review", use_container_width=True)

with right_col:
    st.subheader("YOUR VIDEO GAME REVIEWS")
    for idx, entry in enumerate(st.session_state.review_history):
        if st.button(entry["title"], key=f"history_{idx}_{entry['title']}"):
            st.session_state.selected_history_index = idx

    selected_history_index = st.session_state.selected_history_index
    if selected_history_index is not None and 0 <= selected_history_index < len(st.session_state.review_history):
        entry = st.session_state.review_history[selected_history_index]
        st.markdown(f"### {entry['title']}")
        history_images = entry.get("images", [])
        render_review_with_media(entry["review"], history_images)


if analyze_button:
    if not url.strip():
        st.warning("Please enter a valid Steam store URL.")
    else:
        # Check if age verification needed
        if url and "store.steampowered.com" in url:
            try:
                quick_check = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                if quick_check.status_code == 200 and "birth date" in quick_check.text.lower() and not st.session_state.age_verified:
                    st.error("Please verify your age first by entering your birth date above.")
                    st.stop()
            except:
                pass

        user_images = [f.name for f in uploaded_files] if uploaded_files else None
        initial_state = get_initial_state(
            url,
            user_exp.strip() or None,
            review_rating or None,
            user_images,
            st.session_state.user_birthdate,
        )
        pipeline = get_pipeline()

        with st.status("Generating review...", expanded=True) as status:
            final_state = {}
            for event in pipeline.stream(initial_state, stream_mode="updates"):
                node_name = list(event.keys())[0]
                st.write(f"Completed: **{NODE_LABELS.get(node_name, node_name)}**")
                final_state.update(event[node_name])
            status.update(label="Review complete!", state="complete")

        # Extract game info from final_state
        developer = final_state.get("developer")
        publisher = final_state.get("publisher")
        release_date = final_state.get("release_date")
        steam_rating = final_state.get("steam_rating")
        official_images = final_state.get("official_image")
        official_gifs = final_state.get("official_gif")

        # ── Review ───────────────────────────────────────────────────
        review = final_state.get("review")
        game_title = final_state.get("game_title") or url
        if review:
            st.markdown(f"# **{game_title}**")

            # Collect uploaded images first, then official images, then GIFs
            selected_media = list(uploaded_files or []) + list(official_images or []) + list(official_gifs or [])
            uploaded_image_payloads = [
                {"type": "bytes", "name": file.name, "value": file.getvalue()}
                for file in (uploaded_files or [])
            ]
            official_image_payloads = [
                {"type": "url", "value": image_url}
                for image_url in (official_images or [])
            ]
            review_image_payloads = uploaded_image_payloads + official_image_payloads
            render_review_with_media(review, selected_media)

            # Save to history
            if not any(e["title"] == game_title for e in st.session_state.review_history):
                st.session_state.review_history.append(
                    {"title": game_title, "review": review, "images": review_image_payloads}
                )


            # =========================
            # ✅ ADD PDF BUTTON HERE
            # =========================
            st.divider()
            st.subheader("Export Review")

            pdf_bytes = build_review_pdf(
                game_title=game_title,
                review=review,
                image_sources=review_image_payloads,
            )

            if pdf_bytes:
                st.download_button(
                    "Download Review as PDF",
                    data=pdf_bytes,
                    file_name=f"{game_title.replace(' ', '_')}_review.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_current_review_pdf",
                )
            else:
                st.error(
                    "PDF export failed in this runtime. Make sure Streamlit is running from the project .venv and reportlab is installed there."
                )
        # ── Game Info ────────────────────────────────────────────────
        if any([game_title, developer, publisher, release_date, steam_rating, review_rating, uploaded_files, official_images, official_gifs]):
            with st.expander("GAME INFO", expanded=False):
                if game_title:
                    st.markdown(f"**Title:** {game_title}")
                if publisher:
                    st.markdown(f"**Publisher:** {publisher}")
                if review_rating:
                    st.markdown(f"**Your Rating:** {review_rating}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Developer", developer or "N/A")
                col2.metric("Release Date", release_date or "N/A")
                col3.metric("Steam Rating", steam_rating or "N/A")

                if uploaded_files:
                    st.markdown("#### UPLOADED SCREENSHOTS")
                    cols_per_row = 3
                    for idx in range(0, len(uploaded_files), cols_per_row):
                        cols = st.columns(cols_per_row, gap="small")
                        for col_idx, col in enumerate(cols):
                            if idx + col_idx < len(uploaded_files):
                                img_file = uploaded_files[idx + col_idx]
                                with col:
                                    st.image(img_file, use_container_width=True)

                if official_images:
                    st.markdown("#### OFFICIAL SCREENSHOTS")
                    cols_per_row = 3
                    for idx in range(0, len(official_images), cols_per_row):
                        cols = st.columns(cols_per_row, gap="small")
                        for col_idx, col in enumerate(cols):
                            if idx + col_idx < len(official_images):
                                img_url = official_images[idx + col_idx]
                                with col:
                                    st.image(img_url, use_container_width=True)

                if official_gifs:
                    st.markdown("#### OFFICIAL GIFS / VIDEOS")
                    for gif_url in official_gifs:
                        st.video(gif_url)

        # ── Warnings ─────────────────────────────────────────────────
        for item in final_state.get("warnings", []):
            st.warning(item)