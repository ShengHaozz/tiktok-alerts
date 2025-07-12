"""FastAPI Server for Tiktok authentication

Spins up server to receive authentication code upon installation of tiktok app
"""

from fastapi import Request
from fastapi.responses import HTMLResponse
import httpx
from datetime import datetime
import os
import asyncio
from base_fastapi import App, Service


class AuthApp(App):
    TTS_AUTH_ADDRESS = "https://auth.tiktok-shops.com/api/v2/token/get"
    TTS_REFRESH_ADDRESS = "https://auth.tiktok-shops.com/api/v2/token/refresh"

    def __init__(self, app_key, app_secret):
        super().__init__()
        self.app_key = app_key
        self.app_secret = app_secret
        self.auth_info = {}
        self._token_lock = asyncio.Lock()

        # Register route inside __init__
        self.fastapi_app.get("/tiktokauth", response_class=HTMLResponse)(self.auth_callback)

    async def auth_callback(self, request: Request):
        auth_code = request.query_params.get("code")

        if auth_code:
            self.logger.info(f"Received auth code from Tiktok: {auth_code}")
            tt_partner_auth_status = f"""
            <h1>Authorisation Code Received</h1>
            <p>Code: {auth_code}</p>
            """

            tts_auth_response = await self.tts_auth_request(auth_code)
            if tts_auth_response:
                tts_auth_status = f"""
                <p>
                    Access token: {tts_auth_response.get("access_token")}<br>
                    Access token expire in: {datetime.fromtimestamp(tts_auth_response.get("access_token_expire_in")).strftime("%Y-%m-%d %H:%M:%S")}<br>
                    Refresh token: {tts_auth_response.get("refresh_token")}<br>
                    Refresh token expire in: {datetime.fromtimestamp(tts_auth_response.get("refresh_token_expire_in")).strftime("%Y-%m-%d %H:%M:%S")}
                </p>
                """
                self.auth_info = tts_auth_response.copy()
            else:
                tts_auth_status = "TTS Auth Failed"

        else:
            self.logger.warning("No auth code received from Tiktok")
            tt_partner_auth_status = """
            <h1>No Authorisation Code Received</h1>
            """
            tts_auth_status = ""

        return f"""
        <html>
            <body>
                {tt_partner_auth_status}
                {tts_auth_status}
            </body>
        </html>
        """

    async def tts_auth_request(self, auth_code) -> dict:
        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "auth_code": auth_code,
            "grant_type": "authorized_code",
        }

        async with httpx.AsyncClient() as client:
            try:
                response_json = await client.get(self.TTS_AUTH_ADDRESS, params=params)
                response = response_json.json()
            except Exception as e:
                self.logger.warning(f"TTS Auth Request failed: {e}\nparams: {params}")

                return {}

        if not response or response.get("message") != "success":
            self.logger.warning(
                f"TTS Auth Request not successful:\nresponse: {response}\nparams: {params}"
            )
            return {}

        self.logger.debug(f"TTS Auth returned: {response}")
        return response.get("data", {})

    async def tts_refresh_request(self):
        if (
            datetime.fromtimestamp(self.auth_info.get("refresh_token_expire_in"))
            < datetime.now()
        ):
            self.logger.error("TTS Refresh token expire, please re-install")
            return

        refresh_token = self.auth_info.get("refresh_token")

        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.TTS_REFRESH_ADDRESS, params=params
                ).json()
            except Exception as e:
                self.logger.warning(
                    f"TTS Refresh Request failed: {e}\nparams: {params}"
                )

                return {}

        if not response or response.get("message") != "success":
            self.logger.warning(
                f"TTS Auth Refresh not successful:\nresponse: {response}\nparams: {params}"
            )
            return {}

        self.logger.debug(f"TTS Refresh returned: {response}")
        return response.get("data", {})

    async def get_access_token(self):
        async with self._token_lock:
            while not self.auth_info:
                self.logger.debug("No auth info")
                await asyncio.sleep(5)

        if not self.auth_info.get("access_token_expire_in"):
            self.logger.error("No access token expiry")
            return

        if datetime.now().timestamp() > self.auth_info.get("access_token_expire_in"):
            self.logger.info("Access token expired, refreshing access token")
            self.auth_info = await self.tts_refresh_request()

        return self.auth_info.get("access_token")


class AuthService(Service):
    def __init__(self, app: AuthApp):
        super().__init__(app)
        self.has_retrieved_token = False

    async def get_access_token(self):
        if not self.has_retrieved_token:
            access_token = await self.task_wrapper(self.app_instance.get_access_token)
            self.has_retrieved_token = True
        else:
            access_token = await self.auth_app_instance.get_access_token()

        return access_token


async def main():
    auth_service = AuthService(
        os.getenv("TT_TEST_APP_KEY"), os.getenv("TT_TEST_APP_SECRET")
    )

    access_token = await auth_service.get_access_token()
    print(access_token)

    access_token_2 = await auth_service.get_access_token()
    print(access_token_2)


if __name__ == "__main__":
    asyncio.run(main())
