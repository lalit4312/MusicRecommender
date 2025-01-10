import streamlit as st


def apply_custom_css():
    st.markdown(
        """
        <style>
            /* Global theme */
            :root {
                --background-base: #121212;
                --background-highlight: #1a1a1a;
                --background-press: #000;
                --background-elevated-base: #242424;
                --background-elevated-highlight: #2a2a2a;
                --text-base: #fff;
                --text-subdued: #a7a7a7;
                --essential-base: #fff;
                --essential-subdued: #727272;
                --primary: #1ed760;
            }
            
            /* Main container */
            .stApp {
                background-color: var(--background-base);
                color: var(--text-base);
            }
            
            /* Sidebar */
            .css-1d391kg, .css-1fok5i6 {
                background-color: var(--background-press);
            }
            
            section[data-testid="stSidebar"] {
                background-color: var(--background-press);
                width: 250px;
            }
            
            section[data-testid="stSidebar"] .stButton button {
                width: 100%;
                text-align: left;
                background: none;
                border: none;
                color: var(--text-subdued);
                padding: 8px 16px;
                margin: 4px 0;
                border-radius: 4px;
            }
            
            section[data-testid="stSidebar"] .stButton button:hover {
                background-color: var(--background-elevated-base);
                color: var(--text-base);
            }
            
            /* Main content */
            .main-content {
                background-color: var(--background-base);
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 80px;  /* Space for player */
            }
            
            /* Grid layout for albums */
            .album-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 24px;
                padding: 20px;
            }
            
            .album-card {
                background: var(--background-elevated-base);
                border-radius: 8px;
                padding: 16px;
                transition: background-color 0.3s ease;
            }
            
            .album-card:hover {
                background: var(--background-elevated-highlight);
            }
            
            /* Player bar */
            .player-bar {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: var(--background-press);
                padding: 16px;
                z-index: 1000;
                border-top: 1px solid var(--background-elevated-base);
            }
            
            /* Custom player controls */
            .player-controls {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 16px;
            }
            
            .player-controls button {
                background: none;
                border: none;
                color: var(--text-base);
                cursor: pointer;
            }
            
            /* Progress bar */
            .progress-bar {
                height: 4px;
                background: var(--background-elevated-base);
                border-radius: 2px;
                margin: 8px 0;
            }
            
            .progress {
                height: 100%;
                background: var(--primary);
                border-radius: 2px;
                width: 0%;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def sidebar_navigation():
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 16px;">
                <h1 style="color: white; font-size: 24px;">Music Explorer</h1>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.button("🏠 Home")
        st.button("🎵 Your Library")
        st.button("❤️ Liked Songs")

        st.markdown("<hr/>", unsafe_allow_html=True)
