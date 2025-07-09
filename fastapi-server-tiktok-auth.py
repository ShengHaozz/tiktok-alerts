"""FastAPI Server for Tiktok authentication

Spins up server to receive authentication code upon installation of tiktok app
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from uvicorn import Config, Server
import logging
import requests
from datetime import datetime
import os
import asyncio


class AuthApp:
    app = FastAPI()
    TTS_AUTH_ADDRESS = "https://auth.tiktok-shops.com/api/v2/token/get"

    def __init__(self, app_key, app_secret):
        self.app = FastAPI()
        self.logger = logging.getLogger(__name__)
        self.app_key = app_key
        self.app_secret = app_secret

        # Register route inside __init__
        self.app.get("/tiktokauth", response_class=HTMLResponse)(self.auth_callback)

    async def auth_callback(self, request: Request):
        auth_code = request.query_params.get("code")

        if auth_code:
            self.logger.info(f"Received auth code from Tiktok: {auth_code}")
            tt_partner_auth_status = f"""
            <h1>Authorisation Code Received</h1>
            <p>Code: {auth_code}</p>
            """

            tts_auth_response = self.tts_auth_request(auth_code)
            if tts_auth_response:
                tts_auth_status = f"""
                <p>
                    Access token: {tts_auth_response.get("access_token")}<br>
                    Access token expire in: {datetime.fromtimestamp(tts_auth_response.get("access_token_expire_in")).strftime("%Y-%m-%d %H:%M:%S")}<br>
                    Refresh token: {tts_auth_response.get("refresh_token")}<br>
                    Refresh token expire in: {datetime.fromtimestamp(tts_auth_response.get("refresh_token_expire_in")).strftime("%Y-%m-%d %H:%M:%S")}
                </p>
                """
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

    def tts_auth_request(self, auth_code) -> dict:
        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "auth_code": auth_code,
            "grant_type": "authorized_code",
        }

        self.logger.warning(f"params: {params}")

        try:
            response = requests.get(self.TTS_AUTH_ADDRESS, params=params).json()
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

class AuthService:
    def __init__(self, app_key, app_secret, reload=True):
        self.auth_app_instance = AuthApp(
            app_key=app_key,
            app_secret=app_secret,
        )
        config = Config(app=self.auth_app_instance.app, reload=reload)
        self.server = Server(config)
    
    async def get_coroutine(self):
        await self.server.serve()


if __name__ == "__main__":
    auth_service = AuthService(os.getenv("TT_TEST_APP_KEY"), os.getenv("TT_TEST_APP_SECET"))
    asyncio.run(auth_service.get_coroutine())
