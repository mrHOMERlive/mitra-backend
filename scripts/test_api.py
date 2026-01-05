import requests
import json
from uuid import UUID

BASE_URL = "http://localhost:8000"


def test_create_nda():
    print("=== Testing NDA Creation ===")
    
    payload = {
        "type": "eng",
        "fields": {
            "effective_date": "04.01.2026",
            "company_name": "Test Corporation Ltd",
            "country": "Singapore",
            "registration_number": "TEST123456",
            "signatory_name": "Test User",
            "signatory_title": "CEO",
            "address": "123 Test Street, Singapore",
            "email": "test@example.com"
        }
    }
    
    response = requests.post(f"{BASE_URL}/nda", json=payload)
    
    if response.status_code == 201:
        data = response.json()
        nda_id = data["nda_id"]
        print(f"✓ NDA created successfully")
        print(f"  NDA ID: {nda_id}")
        print(f"  Status: {data['status']}")
        return nda_id
    else:
        print(f"✗ Failed to create NDA: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def test_generate_nda(nda_id: str):
    print(f"\n=== Testing NDA Generation ===")
    
    response = requests.post(f"{BASE_URL}/nda/{nda_id}/generate")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ NDA generated successfully")
        print(f"  Download URL: {data['presigned_url'][:80]}...")
        print(f"  Expires in: {data['expires_in_seconds']} seconds")
        return data["presigned_url"]
    else:
        print(f"✗ Failed to generate NDA: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def test_get_status(nda_id: str):
    print(f"\n=== Testing Get NDA Status ===")
    
    response = requests.get(f"{BASE_URL}/nda/{nda_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status retrieved successfully")
        print(f"  Status: {data['status']}")
        print(f"  Type: {data['type']}")
        return data
    else:
        print(f"✗ Failed to get status: {response.status_code}")
        return None


def test_health():
    print("=== Testing Health Check ===")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print(f"✓ Service is healthy")
        return True
    else:
        print(f"✗ Service health check failed")
        return False


if __name__ == "__main__":
    print("NDA Backend API Test Suite\n")
    
    if not test_health():
        print("\n⚠ Service is not running. Please start the server first:")
        print("  python run.py")
        exit(1)
    
    nda_id = test_create_nda()
    
    if nda_id:
        test_generate_nda(nda_id)
        test_get_status(nda_id)
    
    print("\n✓ Test suite completed!")
