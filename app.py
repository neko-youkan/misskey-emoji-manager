import io
import re
import time
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

import requests
import streamlit as st

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"}
MAX_FILE_SIZE_MB = 10


class MisskeyApiError(RuntimeError):
    pass


@dataclass
class EmojiFile:
    path: str
    filename: str
    data: bytes
    category_from_folder: str


def normalize_server_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if value and not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value


def normalize_emoji_name(filename: str, prefix: str = "") -> str:
    stem = PurePosixPath(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9_+-]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")
    prefix = re.sub(r"[^a-zA-Z0-9_+-]+", "_", prefix.strip()).strip("_").lower()
    name = f"{prefix}_{stem}" if prefix and stem else prefix or stem
    return name[:100]


def request_json(
    method: str,
    url: str,
    *,
    timeout: int = 60,
    expected=(200, 201, 204),
    **kwargs,
) -> Any:
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:
        raise MisskeyApiError(f"通信に失敗しました: {exc}") from exc

    if response.status_code not in expected:
        try:
            body = response.json()
            message = body.get("error", body)
        except ValueError:
            message = response.text[:500]
        raise MisskeyApiError(
            f"HTTP {response.status_code}: {message}"
        )

    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def api_post(server_url: str, endpoint: str, token: str, payload: dict | None = None):
    body = {"i": token}
    if payload:
        body.update(payload)
    return request_json(
        "POST",
        f"{server_url}/api/{endpoint}",
        json=body,
        headers={"Content-Type": "application/json"},
    )


def check_connection(server_url: str, token: str) -> dict:
    result = api_post(server_url, "i", token)
    if not isinstance(result, dict):
        raise MisskeyApiError("ユーザー情報を取得できませんでした。")
    return result


def upload_file(server_url: str, token: str, emoji: EmojiFile) -> str:
    files = {
        "file": (
            emoji.filename,
            io.BytesIO(emoji.data),
            "application/octet-stream",
        )
    }
    data = {
        "i": token,
        "name": emoji.filename,
        "force": "true",
    }
    result = request_json(
        "POST",
        f"{server_url}/api/drive/files/create",
        files=files,
        data=data,
        timeout=120,
    )
    if not isinstance(result, dict) or not result.get("id"):
        raise MisskeyApiError("ファイルは送信されましたが、fileIdを取得できませんでした。")
    return result["id"]


def create_emoji(
    server_url: str,
    token: str,
    *,
    name: str,
    file_id: str,
    category: str,
    aliases: list[str],
    license_text: str,
    is_sensitive: bool,
    local_only: bool,
) -> str:
    common = {
        "name": name,
        "fileId": file_id,
        "category": category or None,
        "aliases": aliases,
        "license": license_text or None,
        "isSensitive": is_sensitive,
        "localOnly": local_only,
    }

    # Misskeyの世代・派生実装によってエンドポイント名や項目が異なるため、
    # 新しい候補から順に試し、未対応なら旧APIへ切り替える。
    attempts = [
        ("emojis/create", common),
        ("admin/emoji/add", {
            "name": name,
            "fileId": file_id,
            "category": category or None,
            "aliases": aliases,
            "license": license_text or None,
        }),
    ]

    errors = []
    for endpoint, payload in attempts:
        try:
            api_post(server_url, endpoint, token, payload)
            return endpoint
        except MisskeyApiError as exc:
            errors.append(f"{endpoint}: {exc}")

    raise MisskeyApiError(" / ".join(errors))


def fetch_existing_names(server_url: str, token: str) -> set[str]:
    names: set[str] = set()

    # 管理者向け一覧API。取得不能な実装では空集合を返し、
    # 実際の登録時エラーを画面に表示する。
    for endpoint, payload in [
        ("admin/emoji/list", {"limit": 100}),
        ("emojis", {}),
    ]:
        try:
            result = api_post(server_url, endpoint, token, payload)
        except MisskeyApiError:
            continue

        rows = result
        if isinstance(result, dict):
            rows = result.get("emojis", result.get("items", []))
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and row.get("name"):
                    names.add(str(row["name"]).lower())
            if names:
                return names
    return names


def read_zip(uploaded_file) -> list[EmojiFile]:
    content = uploaded_file.getvalue()
    emojis = []

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ValueError("ZIPファイルを開けませんでした。") from exc

    for info in archive.infolist():
        if info.is_dir():
            continue

        path = PurePosixPath(info.filename)
        if path.name.startswith(".") or "__MACOSX" in path.parts:
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if info.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            continue

        category = path.parts[-2] if len(path.parts) >= 2 else ""
        emojis.append(
            EmojiFile(
                path=info.filename,
                filename=path.name,
                data=archive.read(info),
                category_from_folder=category,
            )
        )
    return emojis


def parse_aliases(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"[,、\s]+", value)
        if item.strip()
    ]


st.set_page_config(
    page_title="Misskey Emoji Importer",
    page_icon="🌸",
    layout="centered",
)

st.markdown(
    """
    <style>
      .block-container { max-width: 900px; padding-top: 2rem; }
      div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.2);
        border-radius: 16px;
        padding: 14px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌸 Misskey Emoji Importer")
st.caption("ZIP内の画像を、カスタム絵文字としてまとめて登録します。")

with st.expander("① Misskeyへの接続", expanded=True):
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

    if st.button("🔌 接続テスト", use_container_width=True):
        if not server_url or not token:
            st.warning("サーバーURLとAPIトークンを入力してね。")
        else:
            try:
                user = check_connection(server_url, token)
                st.success(
                    f"接続できました：@{user.get('username', 'unknown')}"
                )
            except MisskeyApiError as exc:
                st.error(str(exc))

with st.expander("② ZIPと登録ルール", expanded=True):
    uploaded_zip = st.file_uploader("絵文字ZIP", type=["zip"])
    category = st.text_input(
        "共通カテゴリ",
        placeholder="例：ねこにゃ",
        help="空欄なら、ZIP内の直上フォルダ名をカテゴリとして使えます。",
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
        skip_duplicates = st.checkbox("登録済みの名前をスキップ", value=True)
        is_sensitive = st.checkbox("センシティブとして登録", value=False)
    with col2:
        local_only = st.checkbox("ローカル限定", value=False)
        dry_run = st.checkbox("テスト実行（登録しない）", value=False)

emoji_files = []
if uploaded_zip is not None:
    try:
        emoji_files = read_zip(uploaded_zip)
    except ValueError as exc:
        st.error(str(exc))

if emoji_files:
    st.subheader("登録予定")
    names = [normalize_emoji_name(item.filename, prefix) for item in emoji_files]
    invalid_count = sum(not name for name in names)
    duplicate_in_zip = len(names) - len(set(names))

    col1, col2, col3 = st.columns(3)
    col1.metric("画像", len(emoji_files))
    col2.metric("ZIP内の名前重複", duplicate_in_zip)
    col3.metric("名前変換失敗", invalid_count)

    preview = []
    for item, name in list(zip(emoji_files, names))[:30]:
        final_category = category.strip()
        if not final_category and use_folder_category:
            final_category = item.category_from_folder
        preview.append({
            "ファイル": item.path,
            "絵文字名": name or "⚠ 変換不可",
            "カテゴリ": final_category,
            "サイズ(KB)": round(len(item.data) / 1024, 1),
        })
    st.dataframe(preview, use_container_width=True, hide_index=True)

    if len(preview) < len(emoji_files):
        st.caption(f"先頭30件を表示中。全{len(emoji_files)}件あります。")

st.divider()

start = st.button(
    "🚀 一括インポート開始",
    type="primary",
    use_container_width=True,
    disabled=not emoji_files,
)

if start:
    if not server_url or not token:
        st.error("サーバーURLとAPIトークンを入力してね。")
        st.stop()

    aliases = parse_aliases(aliases_text)
    existing = set()
    if skip_duplicates and not dry_run:
        with st.spinner("登録済み絵文字を確認しています…"):
            existing = fetch_existing_names(server_url, token)

    seen_in_zip = set()
    results = []
    success_count = 0
    skip_count = 0
    fail_count = 0
    progress = st.progress(0)
    status = st.empty()

    for index, emoji in enumerate(emoji_files, start=1):
        name = normalize_emoji_name(emoji.filename, prefix)
        final_category = category.strip()
        if not final_category and use_folder_category:
            final_category = emoji.category_from_folder

        status.write(f"{index}/{len(emoji_files)}　`:{name or '?'}:` を処理中")

        if not name:
            results.append({
                "名前": "",
                "ファイル": emoji.path,
                "結果": "失敗",
                "詳細": "英数字・_・+・-からなる名前に変換できませんでした。",
            })
            fail_count += 1
        elif name in seen_in_zip:
            results.append({
                "名前": name,
                "ファイル": emoji.path,
                "結果": "スキップ",
                "詳細": "ZIP内で同じ絵文字名があります。",
            })
            skip_count += 1
        elif skip_duplicates and name.lower() in existing:
            results.append({
                "名前": name,
                "ファイル": emoji.path,
                "結果": "スキップ",
                "詳細": "同名の絵文字が登録済みです。",
            })
            skip_count += 1
        elif dry_run:
            results.append({
                "名前": name,
                "ファイル": emoji.path,
                "結果": "テストOK",
                "詳細": f"カテゴリ: {final_category or '(なし)'}",
            })
            success_count += 1
        else:
            try:
                file_id = upload_file(server_url, token, emoji)
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
                results.append({
                    "名前": name,
                    "ファイル": emoji.path,
                    "結果": "成功",
                    "詳細": f"{endpoint} で登録",
                })
                success_count += 1
                existing.add(name.lower())
                time.sleep(0.15)
            except MisskeyApiError as exc:
                results.append({
                    "名前": name,
                    "ファイル": emoji.path,
                    "結果": "失敗",
                    "詳細": str(exc),
                })
                fail_count += 1

        seen_in_zip.add(name)
        progress.progress(index / len(emoji_files))

    status.empty()
    st.success(
        f"完了：成功 {success_count}件 / スキップ {skip_count}件 / 失敗 {fail_count}件"
    )
    st.dataframe(results, use_container_width=True, hide_index=True)

    csv_text = "名前,ファイル,結果,詳細\n" + "\n".join(
        '"{}","{}","{}","{}"'.format(
            str(row["名前"]).replace('"', '""'),
            str(row["ファイル"]).replace('"', '""'),
            str(row["結果"]).replace('"', '""'),
            str(row["詳細"]).replace('"', '""'),
        )
        for row in results
    )
    st.download_button(
        "結果CSVを保存",
        csv_text.encode("utf-8-sig"),
        file_name="misskey_emoji_import_result.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.caption(
    "APIトークンはブラウザ内の入力値としてのみ使用し、このアプリ自身は保存しません。"
)
