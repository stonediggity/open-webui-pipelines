import os
from schemas import OpenAIChatMessage
from pydantic import BaseModel
import requests


class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Flowise Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")

        API_URL = "https://flowiseai-railway-production-092d.up.railway.app/api/v1/prediction/70e8ec5f-1d51-42ea-968c-6be37b5275de"

        headers = {}

        payload = {**body, "question": user_message}

        if "user" in payload:
            del payload["user"]
        if "chat_id" in payload:
            del payload["chat_id"]
        if "title" in payload:
            del payload["title"]

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return f"Error: {e}"
