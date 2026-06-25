"""Тонкий клиент для GigaChat API.

GigaChat работает в два шага:
1. Обмен Authorization key на access_token (живёт ~30 минут).
2. Запросы к /chat/completions с этим токеном.

Сертификаты Минцифры могут отсутствовать в системе, поэтому verify
вынесен в настройку (GIGACHAT_VERIFY_SSL).
"""

import os
import time
import uuid
import requests

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class GigaChatError(Exception):
    pass


class GigaChatClient:
    def __init__(self):
        # Authorization key из личного кабинета (base64 client_id:client_secret)
        self.auth_key = os.environ.get("GIGACHAT_AUTH_KEY", "").strip()
        self.scope = os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.model = os.environ.get("GIGACHAT_MODEL", "GigaChat")
        self.verify_ssl = os.environ.get("GIGACHAT_VERIFY_SSL", "false").lower() == "true"
        self._token = None
        self._token_exp = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.auth_key)

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        if not self.auth_key:
            raise GigaChatError("GIGACHAT_AUTH_KEY не задан")

        resp = requests.post(
            OAUTH_URL,
            headers={
                "Authorization": f"Basic {self.auth_key}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"scope": self.scope},
            verify=self.verify_ssl,
            timeout=30,
        )
        if resp.status_code != 200:
            raise GigaChatError(f"OAuth {resp.status_code}: {resp.text}")
        data = resp.json()
        self._token = data["access_token"]
        # expires_at приходит в мс
        self._token_exp = data.get("expires_at", time.time() * 1000 + 1800_000) / 1000
        return self._token

    def chat(self, messages: list[dict], temperature: float = 0.7,
             max_tokens: int = 1200) -> str:
        token = self._get_token()
        resp = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            verify=self.verify_ssl,
            timeout=120,
        )
        if resp.status_code != 200:
            raise GigaChatError(f"Chat {resp.status_code}: {resp.text}")
        return resp.json()["choices"][0]["message"]["content"]


client = GigaChatClient()
