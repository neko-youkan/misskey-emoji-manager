import streamlit as st


def show_home():
    st.markdown(
        """
        <div class="hero-card">
            <h1>🌸 Misskey Emoji Manager</h1>
            <p>
                Misskeyのカスタム絵文字を、もっと簡単に管理するための
                オープンソースツールです。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
    st.markdown("## できること")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <h3>📦 ZIP一括インポート</h3>
                <p>
                    複数の画像をまとめたZIPをアップロードし、
                    Misskeyへ一括登録できます。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🏷️ カテゴリ設定</h3>
                <p>
                    共通カテゴリやZIP内のフォルダ名を使って、
                    絵文字をきれいに分類できます。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🔍 重複スキップ</h3>
                <p>
                    同名の登録済み絵文字や、
                    ZIP内で重複している名前を検出します。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🧪 テスト実行</h3>
                <p>
                    実際に登録する前に、
                    絵文字名やカテゴリの変換結果を確認できます。
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="start-card">
            <span>ℹ️</span>
            左側のメニューから
            <b>📥 Import</b>
            を選んで始めよう。
        </div>
        """,
        unsafe_allow_html=True,
    )