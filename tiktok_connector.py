from tiktok_auth import AuthApp, AuthService
import hmac
import hashlib
from urllib.parse import urlparse
import json
from datetime import datetime, timezone
import os
import asyncio
import httpx
import logging
from enum import Enum
from pydantic import BaseModel


def generate_sign(request_option, app_secret):
    """
    Generate HMAC-SHA256 signature
    :param request_option: Request options dictionary containing qs (query params), uri (path), headers, body etc.
    :param app_secret: Secret key for signing
    :return: Hexadecimal signature string
    """
    # Step 1: Extract and filter query parameters, exclude "access_token" and "sign", sort alphabetically
    params = request_option.get("qs", {})
    exclude_keys = ["access_token", "sign"]
    sorted_params = [
        {"key": key, "value": params[key]}
        for key in sorted(params.keys())
        if key not in exclude_keys
    ]

    # Step 2: Concatenate parameters in {key}{value} format
    param_string = "".join([f"{item['key']}{item['value']}" for item in sorted_params])
    sign_string = param_string

    # Step 3: Append API request path to the signature string
    uri = request_option.get("uri", "")
    pathname = urlparse(uri).path if uri else ""
    sign_string = f"{pathname}{param_string}"

    # Step 4: If not multipart/form-data and request body exists, append JSON-serialized body
    content_type = request_option.get("headers", {}).get("content-type", "")
    body = request_option.get("body", {})
    if content_type != "multipart/form-data" and body:
        body_str = json.dumps(body)  # JSON serialization ensures consistency
        sign_string += body_str

    # Step 5: Wrap signature string with app_secret
    wrapped_string = f"{app_secret}{sign_string}{app_secret}"

    # Step 6: Encode using HMAC-SHA256 and generate hexadecimal signature
    hmac_obj = hmac.new(
        app_secret.encode("utf-8"), wrapped_string.encode("utf-8"), hashlib.sha256
    )
    sign = hmac_obj.hexdigest()
    return sign


class HttpRequestType(Enum):
    GET = "get"
    POST = "post"


class TiktokShop(BaseModel):
    cipher: str
    code: str
    id: int
    name: str
    region: str
    seller_type: str


class TiktokConnector:
    TTS_API_ENDPOINT = "https://open-api.tiktokglobalshop.com"

    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.auth_service = AuthService(
            app=AuthApp(app_key=app_key, app_secret=app_secret)
        )
        self.logger = logging.getLogger(__name__)
        self.shop = None

    async def _get_access_token(self):
        return await self.auth_service.get_access_token()

    async def _generate_api_query(self, uri, qs_kwargs={}, **kwargs):
        headers = {
            "content-type": "application/json",
            "x-tts-access-token": await self._get_access_token(),
        }

        qs = {
            "app_key": self.app_key,
            "sign": "",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        } | qs_kwargs

        request = {
            "headers": headers,
            "qs": qs,
            "uri": uri,
        } | kwargs

        crypto_hash = generate_sign(request, self.app_secret)

        request["qs"]["sign"] = crypto_hash

        return request

    async def _send_https_request(
        self, request: dict, request_type: HttpRequestType = HttpRequestType.GET
    ) -> dict:
        request_url = self.TTS_API_ENDPOINT + request.get("uri")

        async with httpx.AsyncClient() as client:
            try:
                match request_type:
                    case HttpRequestType.GET:
                        response_json = await client.get(
                            request_url,
                            params=request.get("qs"),
                            headers=request.get("headers"),
                        )
                    case HttpRequestType.POST:
                        response_json = await client.post(
                            request_url,
                            params=request.get("qs"),
                            headers=request.get("headers"),
                            data=request.get("body"),
                        )
                response = response_json.json()
            except Exception as e:
                self.logger.warning(
                    f"TTS HTTPS request failed: {e}\nrequest: {request}"
                )
                response = {}

        return response

    async def get_authorized_shops(self):
        query = await self._generate_api_query("/authorization/202309/shops")
        response = await self._send_https_request(query)

        if response.get("message") == "Success" and response.get("data"):
            self.shop = TiktokShop(**response.get("data", {}).get("shops", [{}])[0])
        else:
            self.logger.warning(f"Unable to get authorised shops. Response: {response}")

        return response

    async def search_all_products(self):
        query = await self._generate_api_query(
            "/product/202502/products/search",
            {"shop_cipher": self.shop.cipher, "page_size": 100},
        )

        response = await self._send_https_request(query, HttpRequestType.POST)
        return response


async def main():
    conn = TiktokConnector(
        os.getenv("TT_TEST_APP_KEY"), os.getenv("TT_TEST_APP_SECRET")
    )
    print(await conn.get_authorized_shops())
    print(await conn.search_all_products())


if __name__ == "__main__":
    asyncio.run(main())
