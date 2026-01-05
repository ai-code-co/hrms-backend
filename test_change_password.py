
import requests
import json

AUTH_URL = "http://127.0.0.1:8000/auth"

def test_change_password():
    # 1. Login
    login_url = f"{AUTH_URL}/login/"
    payload = {"username": "admin", "password": "password123"}
    resp = requests.post(login_url, json=payload)
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return

    token = resp.json()['access']
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Change password
    change_url = f"{AUTH_URL}/change-password/"
    # Try correct old password
    payload = {
        "old_password": "password123",
        "new_password": "new_password123",
        "confirm_password": "new_password123"
    }
    
    print("--- Testing Change Password ---")
    resp_change = requests.post(change_url, json=payload, headers=headers)
    print(f"Status: {resp_change.status_code}")
    print(f"Response: {resp_change.json()}")

    if resp_change.status_code == 200:
        # 3. Verify new password works
        print("\n--- Verifying login with NEW password ---")
        payload_new = {"username": "admin", "password": "new_password123"}
        resp_new = requests.post(login_url, json=payload_new)
        print(f"New Login Status: {resp_new.status_code}")
        
        # 4. Reset back to original for future tests
        if resp_new.status_code == 200:
            token_new = resp_new.json()['access']
            headers_new = {"Authorization": f"Bearer {token_new}"}
            payload_reset = {
                "old_password": "new_password123",
                "new_password": "password123",
                "confirm_password": "password123"
            }
            requests.post(change_url, json=payload_reset, headers=headers_new)
            print("--- Password reset to original ---")

if __name__ == "__main__":
    test_change_password()
