import io
from typing import Any

import requests

from utils.emoji_files import EmojiFile


class MisskeyApiError(RuntimeError):
    pass


def normalize_server_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if value and not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value


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


def api_post(
    server_url: str,
    endpoint: str,
    token: str,
    payload: dict | None = None,
):
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


def upload_file(
    server_url: str,
    token: str,
    emoji: EmojiFile,
) -> str:
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
        raise MisskeyApiError(
            "ファイルは送信されましたが、fileIdを取得できませんでした。"
        )

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

    attempts = [
        ("emojis/create", common),
        (
            "admin/emoji/add",
            {
                "name": name,
                "fileId": file_id,
                "category": category or None,
                "aliases": aliases,
                "license": license_text or None,
            },
        ),
    ]

    errors = []

    for endpoint, payload in attempts:
        try:
            api_post(server_url, endpoint, token, payload)
            return endpoint
        except MisskeyApiError as exc:
            errors.append(f"{endpoint}: {exc}")

    raise MisskeyApiError(" / ".join(errors))


def fetch_existing_names(
    server_url: str,
    token: str,
) -> set[str]:
    names: set[str] = set()

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

def fetch_emojis(server_url: str, token: str):
    """
    登録済み絵文字一覧を取得
    """

    for endpoint in [
        "admin/emoji/list",
        "emojis",
    ]:
        try:
            result = api_post(
                server_url,
                endpoint,
                token,
                {"limit": 1000},
            )

            if isinstance(result, list):
                return result

            if isinstance(result, dict):
                if "emojis" in result:
                    return result["emojis"]

                if "items" in result:
                    return result["items"]

        except Exception:
            continue

    return []