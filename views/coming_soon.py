import streamlit as st


def show_coming_soon(
    *,
    icon: str,
    title: str,
    description: str,
    planned_version: str,
):
    st.markdown(
        f"""
        <div class="coming-soon">
            <div class="coming-icon">{icon}</div>
            <h1>{title}</h1>
            <p>{description}</p>
            <p><strong>🚧 Coming Soon</strong></p>
            <p>Version {planned_version}で追加予定</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
