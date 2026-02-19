import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_ID = os.getenv("GROQ_MODEL")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

prompt = "Introduce yourself in a short and crisp way"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

body = {
    "model": MODEL_ID,
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 15,
    "temperature": 0
}

print("Model will start running...")

response = requests.post(GROQ_URL, headers=headers, json=body)
# response.raise_for_status()
response_json = response.json()
print(response_json)
print(response_json["choices"][0]["message"]["content"])
