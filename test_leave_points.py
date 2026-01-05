
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
    return None

def test_leave_points():
    user_name = "medha"
    admin_user = "admin"
    password = "password123"

    user_token = get_token(user_name, password)
    admin_token = get_token(admin_user, password)
    headers_user = {"Authorization": f"Bearer {user_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # --- Point 1: Get assigned & used history ---
    print("\n--- 💰 Point 1: Assigned vs Used History ---")
    resp = requests.get(f"{BASE_URL}/leaves/balance/", headers=headers_user)
    balance = resp.json()['data']['Casual Leave']
    print(f"Allocated (Assigned): {balance['allocated']}")
    print(f"Used: {balance['used']}")
    print(f"Pending: {balance['pending']}")
    print(f"Available: {balance['available']}")

    # --- Point 3: Verification (Applying) ---
    print("\n--- 🏖️ Point 3: Testing Deduction on Apply ---")
    start_bal = balance['pending']
    leave_data = {
        "from_date": "2026-02-01",
        "to_date": "2026-02-01",
        "no_of_days": 1.0,
        "reason": "Test deduction",
        "leave_type": "Casual Leave"
    }
    submit_resp = requests.post(f"{BASE_URL}/leaves/submit-leave/", headers=headers_user, json=leave_data)
    leave_id = submit_resp.json()['data']['leave_id']
    
    resp = requests.get(f"{BASE_URL}/leaves/balance/", headers=headers_user)
    new_bal = resp.json()['data']['Casual Leave']['pending']
    print(f"Pending before: {start_bal}, Pending after apply: {new_bal}")

    # --- Point 3: Verification (Rejection credits back) ---
    print("\n--- ❌ Point 3: Testing Credit back on Reject ---")
    requests.patch(f"{BASE_URL}/leaves/{leave_id}/", headers=headers_admin, json={"status": "Rejected", "rejection_reason": "Testing rejection"})
    resp = requests.get(f"{BASE_URL}/leaves/balance/", headers=headers_user)
    final_bal = resp.json()['data']['Casual Leave']['pending']
    print(f"Pending after reject: {final_bal} (Should be back to {start_bal})")

    # --- Point 2: Cancel pending works ---
    print("\n--- 📂 Point 2: Testing Cancel on Pending ---")
    submit_resp = requests.post(f"{BASE_URL}/leaves/submit-leave/", headers=headers_user, json=leave_data)
    leave_id_2 = submit_resp.json()['data']['leave_id']
    cancel_resp = requests.patch(f"{BASE_URL}/leaves/{leave_id_2}/", headers=headers_user, json={"status": "Cancelled"})
    print(f"Cancel Pending Status: {cancel_resp.status_code} (Expect 200)")

    # --- Point 2: Cancel Approved fails ---
    print("\n--- 🚫 Point 2: Testing Cancel on Approved (Should fail) ---")
    submit_resp = requests.post(f"{BASE_URL}/leaves/submit-leave/", headers=headers_user, json=leave_data)
    leave_id_3 = submit_resp.json()['data']['leave_id']
    # Admin approves
    requests.patch(f"{BASE_URL}/leaves/{leave_id_3}/", headers=headers_admin, json={"status": "Approved"})
    # User tries to cancel
    cancel_resp = requests.patch(f"{BASE_URL}/leaves/{leave_id_3}/", headers=headers_user, json={"status": "Cancelled"})
    print(f"Cancel Approved Status: {cancel_resp.status_code} (Expect 400)")
    if cancel_resp.status_code == 400:
        print(f"Error Message: {cancel_resp.json().get('status', cancel_resp.json())}")

if __name__ == "__main__":
    test_leave_points()
