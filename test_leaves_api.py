
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000/api"
AUTH_URL = "http://127.0.0.1:8000/auth"

def get_token(username, password):
    url = f"{AUTH_URL}/login/"
    payload = {"username": username, "password": password}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Login failed for {username}: {response.text}")
        return None

def test_leaves_flow():
    # Credentials
    user_name = "medha"
    password = "password123"

    print("--- 🔐 Authenticating ---")
    user_token = get_token(user_name, password)

    if not user_token:
        return

    headers_user = {"Authorization": f"Bearer {user_token}"}

    # 1. Check RH Balance & Holidays (Point 2 update)
    print("\n--- 💰 1. Checking Dedicated RH Balance & Holidays ---")
    rh_bal_resp = requests.get(f"{BASE_URL}/leaves/rh-balance/", headers=headers_user)
    print(f"Status: {rh_bal_resp.status_code}")
    print(json.dumps(rh_bal_resp.json(), indent=2))

    # 2. Submit RH Leave to verify it still works with the new structure
    print("\n--- 🏖️ 2. Submitting RH Leave ---")
    rh_data = {
        "from_date": "2026-01-14",
        "to_date": "2026-01-14",
        "no_of_days": 1.0,
        "reason": "Test RH",
        "leave_type": "Restricted Holiday",
        "rh_id": 1
    }
    submit_resp = requests.post(f"{BASE_URL}/leaves/submit-leave/", headers=headers_user, json=rh_data)
    print(f"Status: {submit_resp.status_code}")
    print(json.dumps(submit_resp.json(), indent=2))

if __name__ == "__main__":
    test_leaves_flow()
