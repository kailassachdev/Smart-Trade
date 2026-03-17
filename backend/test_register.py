from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
try:
    response = client.post(
        "/register",
        json={"username": "testuser5", "password": "password"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error caught directly:")
    import traceback
    traceback.print_exc()
