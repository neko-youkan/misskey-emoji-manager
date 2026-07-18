import streamlit as st

from styles import apply_app_style
from views.coming_soon import show_coming_soon
from views.emoji_list import show_emoji_list
from views.home import show_home
from views.import_page import show_import_page


APP_VERSION = "1.1.0"
LOGO_PATH = "assets/logo.png"


st.set_page_config(
    page_title="Misskey Emoji Manager",
    page_icon=LOGO_PATH,
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_app_style()


with st.sidebar:
    # ------------------------
    # ブランドロゴ
    # ------------------------
    logo_left, logo_center, logo_right = st.columns([1, 2, 1])

    with logo_center:
        st.image(
            LOGO_PATH,
            width=140,
        )

    st.markdown(
        "<h2 style='text-align:center; margin-bottom:0;'>neko-youkan</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style="
            text-align:center;
            color:#aab2c0;
            margin-top:4px;
            margin-bottom:22px;
            font-size:0.9rem;
        ">
            Misskey Emoji Manager
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------
    # メニュー
    # ------------------------
    page = st.radio(
        "メニュー",
        [
            "🏠 Home",
            "📦 Import",
            "🏷️ Emoji List",
            "🗑️ Delete",
            "💾 Export",
            "⚙️ Settings",
        ],
        label_visibility="collapsed",
    )

    # ------------------------
    # フッター
    # ------------------------
    st.divider()

    st.markdown(
        f"""
        <div style="
            color:#aab2c0;
            font-size:0.85rem;
            line-height:1.9;
        ">
            v{APP_VERSION}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------
# ページ切り替え
# ------------------------
if page == "🏠 Home":
    show_home()

elif page == "📦 Import":
    show_import_page()

elif page == "🏷️ Emoji List":
    show_emoji_list()

elif page == "🗑️ Delete":
    show_coming_soon(
        icon="🗑️",
        title="Delete",
        description=(
            "複数の絵文字を選択して、"
            "一括削除できる機能です。"
        ),
        planned_version="1.2.0",
    )

elif page == "💾 Export":
    show_coming_soon(
        icon="💾",
        title="Export",
        description=(
            "登録済みの絵文字を"
            "ZIP形式で保存する機能です。"
        ),
        planned_version="2.0.0",
    )

else:
    show_coming_soon(
        icon="⚙️",
        title="Settings",
        description=(
            "接続情報や表示方法を管理する"
            "設定画面です。"
        ),
        planned_version="2.0.0",
    )