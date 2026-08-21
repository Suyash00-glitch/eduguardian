import requests
import json

base_url = "http://localhost:5000"

print("--- 1. Inspecting Live OpenAPI Schema on :5000 ---")
try:
    r = requests.get(f"{base_url}/openapi.json", timeout=5)
    print(f"OpenAPI Status: {r.status_code}")
    if r.status_code == 200:
        schema = r.json()
        paths = list(schema.get("paths", {}).keys())
        print(f"Total Routes in FastAPI: {len(paths)}")
        print("Auth Routes:")
        for p in paths:
            if "auth" in p or "portal" in p:
                methods = list(schema["paths"][p].keys())
                print(f"  {methods} -> {p}")
        
        has_portal_login = "/api/auth/portal-login" in paths
        print(f"\n>> /api/auth/portal-login in OpenAPI: {has_portal_login}")
except Exception as e:
    print("Error fetching openapi.json:", e)

print("\n--- 2. Testing Live POST /api/auth/portal-login ---")
try:
    payload = {
        "mobile": "9999999999",
        "password": "sample_password_123",
        "captcha": "123456",
        "terms_accepted": True
    }
    r = requests.post(f"{base_url}/api/auth/portal-login", json=payload, timeout=10)
    print(f"Live Status Code: {r.status_code}")
    print(f"Live Response Body: {r.text}")
except Exception as e:
    print("Error testing portal-login:", e)
