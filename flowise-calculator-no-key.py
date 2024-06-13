from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests

class Pipeline:
    class Valves(BaseModel):
        pass  # No API key needed for Flowise API

    def __init__(self):
        self.name = "Flowise Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"on_startup:{__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")

        print(messages)
        print(user_message)

        API_URL = "https://flowiseai-railway-production-092d.up.railway.app/api/v1/prediction/70e8ec5f-1d51-42ea-968c-6be37b5275de"

        headers = {
            "Content-Type": "application/json"
        }

        # Creating the payload based on your example
        payload = {
            "question": user_message
        }

        print(payload)

        try:
            r = requests.post(
                url=API_URL,
                json=payload,
                headers=headers,
                stream=True,
            )

            r.raise_for_status()

            if body.get("stream"):
                for line in r.iter_lines():
                    yield line.decode('utf-8')
            else:
                response_json = r.json()
                # Raise an exception if "text" is not in the response
                if "text" not in response_json:
                    raise ValueError("No 'text' in the response")
                return response_json["text"]
        except Exception as e:
            return f"Error: {e}"
