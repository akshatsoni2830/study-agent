import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Get API key and model name from environment variables
api_key = os.getenv('GEMINI_API_KEY', '').strip('"\'')
model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-pro').strip('"\'')

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"Testing with model: {model_name}")

# Prepare the API request
url = f'https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}'
headers = {'Content-Type': 'application/json'}
data = {
    'contents': [{
        'role': 'user',
        'parts': [{'text': 'Say hello'}]
    }]
}

try:
    # Make the API request
    print("Sending request to Gemini API...")
    response = requests.post(url, headers=headers, json=data)
    
    # Print the response
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! API is working correctly.")
        print("Response:", response.json())
    else:
        print("Error response from API:")
        print(response.text)
        
except Exception as e:
    print(f"An error occurred: {str(e)}")