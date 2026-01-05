
import requests
import json

AUTH_URL = "http://127.0.0.1:8000/auth"

def test_token_refresh():
    # 1. Login
    login_url = f"{AUTH_URL}/login/"
    payload = {"username": "admin", "password": "password123"}
    resp = requests.post(login_url, json=payload)
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return

    tokens = resp.json()
    access_1 = tokens['access']
    refresh_1 = tokens['refresh']
    
    print(f"Initial Refresh Token: {refresh_1[:20]}...")

    # 2. Refresh tokens
    refresh_url = f"{AUTH_URL}/refresh-token/"
    payload = {"refresh": refresh_1}
    resp_ref = requests.post(refresh_url, json=payload)
    
    if resp_ref.status_code != 200:
        print(f"Refresh failed: {resp_ref.text}")
        return
    
    tokens_2 = resp_ref.json()
    access_2 = tokens_2.get('access')
    refresh_2 = tokens_2.get('refresh')
    
    print(f"New Access Token: {access_2[:20]}...")
    if refresh_2:
        print(f"New Refresh Token: {refresh_2[:20]}...")
        if refresh_1 == refresh_2:
            print("✅ Refresh token remains the same (Rotation is OFF)")
        else:
            print("❌ Refresh token CHANGED (Rotation is ON)")
    else:
        print("✅ No new refresh token returned (Standard behavior when Rotation is OFF)")

if __name__ == "__main__":
    test_token_refresh()
