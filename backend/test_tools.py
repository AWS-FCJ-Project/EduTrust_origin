import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_tutor_datetime():
    print("\n--- Testing Tutor Agent (Datetime) ---")
    payload = {
        "question": "What is the current date and time right now?"
    }
    try:
        response = requests.post(f"{BASE_URL}/tutor/ask", json=payload)
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_tutor_search():
    print("\n--- Testing Tutor Agent (Web Search) ---")
    payload = {
        "question": "What is the latest version of Python available as of late 2024/2025?"
    }
    try:
        response = requests.post(f"{BASE_URL}/tutor/ask", json=payload)
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Wait a bit to ensure server is ready if it was just started
    # time.sleep(2)
    test_tutor_datetime()
    test_tutor_search()
