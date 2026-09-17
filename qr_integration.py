import os

import requests


# =========================================================
# SETTINGS
# =========================================================

def get_qr_settings():

    qr_api_url = os.getenv(
        "QR_API_URL",
        "",
    ).strip().rstrip("/")

    integration_secret = os.getenv(
        "QR_INTEGRATION_SECRET",
        "",
    ).strip()

    if not qr_api_url:
        raise RuntimeError(
            "QR_API_URL is not configured"
        )

    if not integration_secret:
        raise RuntimeError(
            "QR_INTEGRATION_SECRET is not configured"
        )

    return (
        qr_api_url,
        integration_secret,
    )


# =========================================================
# GENERIC QR REGISTRATION
# =========================================================

def register_qr_guest(
        site,
        registration_id,
        name,
        phone,
        email,
):

    site = (
            site
            or ""
    ).strip().lower()

    if site not in {
        "decora",
        "prestige",
    }:
        raise ValueError(
            f"Unsupported QR site: {site}"
        )

    if not registration_id:
        raise ValueError(
            "registration_id is required"
        )

    name = (
            name
            or ""
    ).strip()

    phone = (
            phone
            or ""
    ).strip()

    email = (
            email
            or ""
    ).strip().lower()

    if not name:
        raise ValueError(
            "name is required"
        )

    if not email:
        raise ValueError(
            "email is required"
        )

    (
        qr_api_url,
        integration_secret,
    ) = get_qr_settings()

    try:

        response = requests.post(
            (
                f"{qr_api_url}"
                "/internal/register"
            ),
            json={
                "site": site,
                "registration_id": (
                    registration_id
                ),
                "name": name,
                "phone": phone,
                "email": email,
            },
            headers={
                "X-QR-Integration-Key":
                    integration_secret,
            },
            timeout=10,
        )

    except requests.RequestException as exc:

        raise RuntimeError(
            (
                "Could not connect "
                "to QR system: "
                f"{exc}"
            )
        ) from exc

    try:

        result = response.json()

    except ValueError as exc:

        raise RuntimeError(
            (
                "QR system returned "
                "invalid JSON. "
                f"HTTP {response.status_code}"
            )
        ) from exc

    if not response.ok:

        error_message = (
                result.get("error")
                or result.get("message")
                or (
                    "QR API request failed "
                    f"with HTTP "
                    f"{response.status_code}"
                )
        )

        raise RuntimeError(
            error_message
        )

    if not result.get("ok"):

        raise RuntimeError(
            result.get(
                "error",
                "QR integration failed",
            )
        )

    return result


# =========================================================
# DECORA
# =========================================================

def register_decora_guest(
        registration_id,
        name,
        phone,
        email,
):

    return register_qr_guest(
        site="decora",
        registration_id=(
            registration_id
        ),
        name=name,
        phone=phone,
        email=email,
    )


# =========================================================
# PRESTIGE DESIGN
# =========================================================

def register_prestige_guest(
        registration_id,
        name,
        phone,
        email,
):

    return register_qr_guest(
        site="prestige",
        registration_id=(
            registration_id
        ),
        name=name,
        phone=phone,
        email=email,
    )
