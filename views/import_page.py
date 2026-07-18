import time

import streamlit as st

from services.misskey_api import (
    MisskeyApiError,
    check_connection,
    create_emoji,
    fetch_existing_names,
    normalize_server_url,
    upload_file,
)
from utils.emoji_files import (
    normalize_emoji_name,
    parse_aliases,
    read_zip,
)


def show_import_page():
    st.title("📥 ZIP Import")
    st.caption("ZIP内の画像を、Misskeyのカスタム絵文字としてまとめて登録します。")

    with st.expander("🔗 サーバー接続", expanded=True):
        server_url = normalize_server_url(
            st.text_input(
                "サーバーURL",
                placeholder="https://example.com",
            )
        )

        token = st.text_input(
            "APIトークン",
            type="password",
            help="管理者権限を持つアカウントのAPIトークンを使います。",
        )

        if st.button(
            "🔌 接続テスト",
            use_container_width=True,
        ):
            if not server_url or not token:
                st.warning(
                    "サーバーURLとAPIトークンを入力してね。"
                )
            else:
                try:
                    user = check_connection(server_url, token)
                    st.success(
                        f"接続できました："
                        f"@{user.get('username', 'unknown')}"
                    )
                except MisskeyApiError as exc:
                    st.error(str(exc))

    with st.expander("📦 インポート設定", expanded=True):
        uploaded_zip = st.file_uploader(
            "絵文字ZIP",
            type=["zip"],
        )

        category = st.text_input(
            "共通カテゴリ",
            placeholder="例：ねこにゃ",
            help=(
                "空欄なら、ZIP内の直上フォルダ名を"
                "カテゴリとして使えます。"
            ),
        )

        use_folder_category = st.checkbox(
            "共通カテゴリが空欄ならフォルダ名をカテゴリにする",
            value=True,
        )

        prefix = st.text_input(
            "絵文字名の接頭辞",
            placeholder="例：neco",
            help="neko.png → neco_neko のようになります。",
        )

        aliases_text = st.text_input(
            "全絵文字に付けるエイリアス",
            placeholder="cat, neko",
        )

        license_text = st.text_input(
            "ライセンス",
            placeholder="作者名・配布元・利用条件など",
        )

        col1, col2 = st.columns(2)

        with col1:
            skip_duplicates = st.checkbox(
                "登録済みの名前をスキップ",
                value=True,
            )
            is_sensitive = st.checkbox(
                "センシティブとして登録",
                value=False,
            )

        with col2:
            local_only = st.checkbox(
                "ローカル限定",
                value=False,
            )
            dry_run = st.checkbox(
                "テスト実行（登録しない）",
                value=False,
            )

    emoji_files = []

    if uploaded_zip is not None:
        try:
            emoji_files = read_zip(uploaded_zip)
        except ValueError as exc:
            st.error(str(exc))

    if emoji_files:
        st.subheader("📋 登録予定")

        names = [
            normalize_emoji_name(item.filename, prefix)
            for item in emoji_files
        ]

        invalid_count = sum(not name for name in names)
        duplicate_in_zip = len(names) - len(set(names))

        col1, col2, col3 = st.columns(3)
        col1.metric("画像", len(emoji_files))
        col2.metric("ZIP内の名前重複", duplicate_in_zip)
        col3.metric("名前変換失敗", invalid_count)

        preview = []

        for item, name in list(
            zip(emoji_files, names)
        )[:30]:
            final_category = category.strip()

            if not final_category and use_folder_category:
                final_category = item.category_from_folder

            preview.append(
                {
                    "ファイル": item.path,
                    "絵文字名": name or "⚠ 変換不可",
                    "カテゴリ": final_category,
                    "サイズ(KB)": round(
                        len(item.data) / 1024,
                        1,
                    ),
                }
            )

        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
        )

        if len(preview) < len(emoji_files):
            st.caption(
                f"先頭30件を表示中。"
                f"全{len(emoji_files)}件あります。"
            )

    st.divider()

    start = st.button(
        "🚀 一括インポート開始",
        type="primary",
        use_container_width=True,
        disabled=not emoji_files,
    )

    if start:
        run_import(
            emoji_files=emoji_files,
            server_url=server_url,
            token=token,
            prefix=prefix,
            category=category,
            use_folder_category=use_folder_category,
            aliases_text=aliases_text,
            license_text=license_text,
            skip_duplicates=skip_duplicates,
            is_sensitive=is_sensitive,
            local_only=local_only,
            dry_run=dry_run,
        )

    st.markdown(
        """
        <div class="security-note">
            🔐 APIトークンはブラウザ内の入力値としてのみ使用し、
            このアプリ自身は保存しません。
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_import(
    *,
    emoji_files,
    server_url,
    token,
    prefix,
    category,
    use_folder_category,
    aliases_text,
    license_text,
    skip_duplicates,
    is_sensitive,
    local_only,
    dry_run,
):
    if not server_url or not token:
        st.error(
            "サーバーURLとAPIトークンを入力してね。"
        )
        return

    aliases = parse_aliases(aliases_text)
    existing = set()

    if skip_duplicates and not dry_run:
        with st.spinner(
            "登録済み絵文字を確認しています…"
        ):
            existing = fetch_existing_names(
                server_url,
                token,
            )

    seen_in_zip = set()
    results = []

    success_count = 0
    skip_count = 0
    fail_count = 0

    progress = st.progress(0)
    status = st.empty()

    for index, emoji in enumerate(
        emoji_files,
        start=1,
    ):
        name = normalize_emoji_name(
            emoji.filename,
            prefix,
        )

        final_category = category.strip()

        if not final_category and use_folder_category:
            final_category = emoji.category_from_folder

        status.write(
            f"{index}/{len(emoji_files)}　"
            f"`:{name or '?'}:` を処理中"
        )

        if not name:
            results.append(
                {
                    "名前": "",
                    "ファイル": emoji.path,
                    "結果": "失敗",
                    "詳細": (
                        "英数字・_・+・-からなる名前に"
                        "変換できませんでした。"
                    ),
                }
            )
            fail_count += 1

        elif name in seen_in_zip:
            results.append(
                {
                    "名前": name,
                    "ファイル": emoji.path,
                    "結果": "スキップ",
                    "詳細": (
                        "ZIP内で同じ絵文字名があります。"
                    ),
                }
            )
            skip_count += 1

        elif (
            skip_duplicates
            and name.lower() in existing
        ):
            results.append(
                {
                    "名前": name,
                    "ファイル": emoji.path,
                    "結果": "スキップ",
                    "詳細": (
                        "同名の絵文字が登録済みです。"
                    ),
                }
            )
            skip_count += 1

        elif dry_run:
            results.append(
                {
                    "名前": name,
                    "ファイル": emoji.path,
                    "結果": "テストOK",
                    "詳細": (
                        f"カテゴリ: "
                        f"{final_category or '(なし)'}"
                    ),
                }
            )
            success_count += 1

        else:
            try:
                file_id = upload_file(
                    server_url,
                    token,
                    emoji,
                )

                endpoint = create_emoji(
                    server_url,
                    token,
                    name=name,
                    file_id=file_id,
                    category=final_category,
                    aliases=aliases,
                    license_text=license_text.strip(),
                    is_sensitive=is_sensitive,
                    local_only=local_only,
                )

                results.append(
                    {
                        "名前": name,
                        "ファイル": emoji.path,
                        "結果": "成功",
                        "詳細": (
                            f"{endpoint} で登録"
                        ),
                    }
                )

                success_count += 1
                existing.add(name.lower())
                time.sleep(0.15)

            except MisskeyApiError as exc:
                results.append(
                    {
                        "名前": name,
                        "ファイル": emoji.path,
                        "結果": "失敗",
                        "詳細": str(exc),
                    }
                )
                fail_count += 1

        seen_in_zip.add(name)
        progress.progress(
            index / len(emoji_files)
        )

    status.empty()

    st.success(
        f"完了：成功 {success_count}件 / "
        f"スキップ {skip_count}件 / "
        f"失敗 {fail_count}件"
    )

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True,
    )

    csv_text = (
        "名前,ファイル,結果,詳細\n"
        + "\n".join(
            '"{}","{}","{}","{}"'.format(
                str(row["名前"]).replace(
                    '"',
                    '""',
                ),
                str(row["ファイル"]).replace(
                    '"',
                    '""',
                ),
                str(row["結果"]).replace(
                    '"',
                    '""',
                ),
                str(row["詳細"]).replace(
                    '"',
                    '""',
                ),
            )
            for row in results
        )
    )

    st.download_button(
        "結果CSVを保存",
        csv_text.encode("utf-8-sig"),
        file_name=(
            "misskey_emoji_import_result.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )
