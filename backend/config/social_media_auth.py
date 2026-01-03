from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Iterable


def _split_tokens(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class PlatformCredentials:
    platform: str
    tokens: list[str]


class SocialMediaAuthManager:
    """Loads credentials from the environment.

    Supports multiple accounts per platform by allowing comma-separated values.
    Tokens may optionally be encrypted using Fernet and stored as
    ENC(<base64-encoded-ciphertext>). If cryptography is not installed, encrypted
    values cannot be decrypted.
    """

    def __init__(self, env: dict[str, str] | None = None):
        self._env = env or dict(os.environ)
        self._token_index: dict[str, int] = {}

    def get_tokens(self, platform: str) -> list[str]:
        key = f"{platform.upper()}_TOKENS"
        single_key = f"{platform.upper()}_TOKEN"
        raw = self._env.get(key) or self._env.get(single_key)
        if not raw:
            return []
        raw = raw.strip()
        # Support ENV values like ENC(...)
        if raw.startswith("ENC(") and raw.endswith(")"):
            raw = self._decrypt_fernet(raw[4:-1])
        return _split_tokens(raw)

    def get_token_round_robin(self, platform: str) -> str | None:
        tokens = self.get_tokens(platform)
        if not tokens:
            return None
        idx = self._token_index.get(platform, 0) % len(tokens)
        self._token_index[platform] = idx + 1
        return tokens[idx]

    def _decrypt_fernet(self, b64_ciphertext: str) -> str:
        secret = self._env.get("SOCIAL_MEDIA_FERNET_KEY")
        if not secret:
            raise RuntimeError(
                "Encrypted token provided but SOCIAL_MEDIA_FERNET_KEY is not set"
            )
        try:
            from cryptography.fernet import Fernet
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "cryptography is required to decrypt ENC(...) credentials"
            ) from e

        f = Fernet(secret.encode("utf-8"))
        plaintext = f.decrypt(base64.b64decode(b64_ciphertext))
        return plaintext.decode("utf-8")


def encrypt_for_env(plaintext: str, fernet_key: str) -> str:
    """Helper to generate an ENC(...) string for storing in .env."""

    from cryptography.fernet import Fernet

    f = Fernet(fernet_key.encode("utf-8"))
    ciphertext = f.encrypt(plaintext.encode("utf-8"))
    return f"ENC({base64.b64encode(ciphertext).decode('utf-8')})"


def load_dotenv_if_available(path: str = ".env") -> None:
    try:
        from dotenv import load_dotenv
    except Exception:  # pragma: no cover
        return

    load_dotenv(path)


def iter_supported_platform_env_vars(platforms: Iterable[str]) -> list[str]:
    vars_: list[str] = ["SOCIAL_MEDIA_FERNET_KEY"]
    for p in platforms:
        vars_.append(f"{p.upper()}_TOKENS")
        vars_.append(f"{p.upper()}_TOKEN")
        vars_.append(f"{p.upper()}_CLIENT_ID")
        vars_.append(f"{p.upper()}_CLIENT_SECRET")
        vars_.append(f"{p.upper()}_ACCESS_TOKEN")
    return vars_
