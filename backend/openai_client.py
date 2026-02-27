import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful AI chatbot for social platforms."
)

FAST_MODEL = os.getenv("FAST_MODEL", "phi3")
SMART_MODEL = os.getenv("SMART_MODEL", "llama3")


def get_ai_response(user_message, mode="fast"):
    model = FAST_MODEL if mode == "fast" else SMART_MODEL

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "options": {
            "temperature": 0.3 if mode == "fast" else 0.7,
            "num_predict": 128 if mode == "fast" else 256
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError("Ollama is not responding")

    return response.json()["message"]["content"]
