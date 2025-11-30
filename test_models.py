# test_models.py
import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
response = requests.get(url)

if response.status_code == 200:
    models = response.json().get("models", [])
    print("Available models:")
    for model in models:
        print(f"- {model['name']} (supports: {', '.join(model.get('supportedGenerationMethods', []))})")
else:
    print(f"Error listing models: {response.status_code}")
    print(response.text)