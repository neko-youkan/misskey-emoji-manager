import pandas as pd
import streamlit as st

from services.misskey_api import (
    MisskeyApiError,
    fetch_emojis,
    normalize_server_url,
)


def show_emoji_list():
    st.title("🏷️ Emoji List")

    st.markdown(
        """
        <div class="page-intro">
            登録済みのカスタム絵文字を確認・検索できます。
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------
    # サーバー接続
    # ------------------------
    with st.expander("🔗 サーバー接続", expanded=True):
        server_url = normalize_server_url(
            st.text_input(
                "サーバーURL",
                placeholder="https://example.com",
                key="emoji_list_server_url",
            )
        )

        token = st.text_input(
            "APIトークン",
            type="password",
            help="管理者権限を持つアカウントのAPIトークンを使います。",
            key="emoji_list_api_token",
        )

        load_button = st.button(
            "🏷️ 絵文字一覧を取得",
            type="primary",
            use_container_width=True,
        )

    # ------------------------
    # 一覧を取得
    # ------------------------
    if load_button:
        if not server_url or not token:
            st.warning(
                "サーバーURLとAPIトークンを入力してね。"
            )
            return

        try:
            with st.spinner(
                "登録済みの絵文字を取得しています…"
            ):
                emojis = fetch_emojis(
                    server_url,
                    token,
                )

            st.session_state["emoji_list_data"] = emojis

        except MisskeyApiError as exc:
            st.error(str(exc))
            return

        except Exception as exc:
            st.error(
                f"絵文字一覧の取得に失敗しました：{exc}"
            )
            return

    # ------------------------
    # 取得済みデータ
    # ------------------------
    emojis = st.session_state.get(
        "emoji_list_data",
        [],
    )

    if not emojis:
        st.info(
            "サーバーURLとAPIトークンを入力して、"
            "「絵文字一覧を取得」を押してね。"
        )
        return

    # ------------------------
    # 検索・絞り込み
    # ------------------------
    search_col, category_col = st.columns([2, 1])

    with search_col:
        search_query = st.text_input(
            "🔍 絵文字を検索",
            placeholder="名前・カテゴリ・エイリアスで検索...",
            key="emoji_search",
        )

    categories = sorted(
        {
            str(emoji.get("category", "")).strip()
            for emoji in emojis
            if str(emoji.get("category", "")).strip()
        }
    )

    with category_col:
        selected_category = st.selectbox(
            "📁 カテゴリ",
            ["すべて"] + categories,
            key="emoji_category_filter",
        )

    filtered_emojis = filter_emojis(
        emojis=emojis,
        search_query=search_query,
        selected_category=selected_category,
    )

    # ------------------------
    # 件数表示
    # ------------------------
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric(
            "登録済み",
            len(emojis),
        )

    with metric_col2:
        st.metric(
            "表示中",
            len(filtered_emojis),
        )

    with metric_col3:
        st.metric(
            "カテゴリ",
            len(categories),
        )

    st.divider()

    if not filtered_emojis:
        st.warning(
            "検索条件に一致する絵文字がありません。"
        )
        return

    # ------------------------
    # DataFrame作成
    # ------------------------
    rows = []

    for emoji in filtered_emojis:
        aliases = emoji.get("aliases", [])

        if not isinstance(aliases, list):
            aliases = []

        image_url = (
            emoji.get("url")
            or emoji.get("publicUrl")
            or emoji.get("uri")
            or ""
        )

        rows.append(
            {
                "選択": False,
                "画像": image_url,
                "名前": f":{emoji.get('name', '名前なし')}:",
                "カテゴリ": emoji.get("category") or "なし",
                "エイリアス": ", ".join(
                    str(alias)
                    for alias in aliases
                ),
                "ID": emoji.get(
                    "id",
                    emoji.get("name", ""),
                ),
            }
        )

    emoji_df = pd.DataFrame(rows)

    # ------------------------
    # 一覧表
    # ------------------------
    edited_df = st.data_editor(
        emoji_df,
        use_container_width=True,
        hide_index=True,
        height=600,
        row_height=72,
        column_order=[
            "選択",
            "画像",
            "名前",
            "カテゴリ",
            "エイリアス",
        ],
        column_config={
            "選択": st.column_config.CheckboxColumn(
                "選択",
                help="編集・削除する絵文字を選択します。",
                default=False,
                width="small",
            ),
            "画像": st.column_config.ImageColumn(
                "画像",
                help="カスタム絵文字のプレビュー",
                width="small",
            ),
            "名前": st.column_config.TextColumn(
                "名前",
                width="medium",
            ),
            "カテゴリ": st.column_config.TextColumn(
                "カテゴリ",
                width="medium",
            ),
            "エイリアス": st.column_config.TextColumn(
                "エイリアス",
                width="large",
            ),
            "ID": None,
        },
        disabled=[
            "画像",
            "名前",
            "カテゴリ",
            "エイリアス",
            "ID",
        ],
        key="emoji_list_editor",
    )

    # ------------------------
    # 選択中の絵文字
    # ------------------------
    selected_rows = edited_df[
        edited_df["選択"] == True
    ]

    selected_count = len(selected_rows)

    st.caption(
        f"{selected_count}件選択中"
    )

    action_col1, action_col2, action_col3 = st.columns(
        [1, 1, 2]
    )

    with action_col1:
        edit_button = st.button(
            "✏️ Edit",
            use_container_width=True,
            disabled=selected_count != 1,
        )

    with action_col2:
        delete_button = st.button(
            "🗑️ Delete",
            use_container_width=True,
            disabled=selected_count == 0,
        )

    with action_col3:
        clear_button = st.button(
            "選択を解除",
            use_container_width=True,
            disabled=selected_count == 0,
        )

    # ------------------------
    # 仮の操作メッセージ
    # ------------------------
    if edit_button:
        selected_name = selected_rows.iloc[0]["名前"]

        st.info(
            f"{selected_name} の編集機能は次に実装します。"
        )

    if delete_button:
        selected_names = selected_rows[
            "名前"
        ].tolist()

        st.warning(
            f"{len(selected_names)}件を選択しています。"
            "削除機能は次に実装します。"
        )

        st.code(
            "\n".join(selected_names)
        )

    if clear_button:
        st.session_state.pop(
            "emoji_list_editor",
            None,
        )
        st.rerun()

    st.markdown(
        """
        <div class="security-note">
            🔐 APIトークンはブラウザ内の入力値としてのみ使用し、
            このアプリ自身は保存しません。
        </div>
        """,
        unsafe_allow_html=True,
    )


def filter_emojis(
    emojis,
    search_query,
    selected_category,
):
    search_text = search_query.strip().lower()
    filtered_emojis = []

    for emoji in emojis:
        name = str(
            emoji.get("name", "")
        ).lower()

        category = str(
            emoji.get("category", "")
        ).strip()

        aliases = emoji.get("aliases", [])

        if not isinstance(aliases, list):
            aliases = []

        aliases_text = " ".join(
            str(alias).lower()
            for alias in aliases
        )

        searchable_text = (
            f"{name} "
            f"{category.lower()} "
            f"{aliases_text}"
        )

        matches_search = (
            not search_text
            or search_text in searchable_text
        )

        matches_category = (
            selected_category == "すべて"
            or category == selected_category
        )

        if matches_search and matches_category:
            filtered_emojis.append(emoji)

    return filtered_emojis