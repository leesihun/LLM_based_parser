#!/usr/bin/env python3
"""Quick test to verify the /api/chat/with-json endpoint works."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_json_endpoint():
    """Test the /api/chat/with-json endpoint with sample data."""
    from backend.app import create_app

    app = create_app()
    client = app.test_client()

    # Test data
    test_cases = [
        {
            "name": "Simple numeric array",
            "payload": {
                "message": "What is the sum of all values?",
                "json_data": {
                    "values": [10, 20, 30, 40, 50]
                }
            }
        },
        {
            "name": "Nested objects with numeric fields",
            "payload": {
                "message": "Which product has the highest price?",
                "json_data": {
                    "products": [
                        {"id": 1, "name": "Widget", "price": 19.99},
                        {"id": 2, "name": "Gadget", "price": 49.99},
                        {"id": 3, "name": "Doohickey", "price": 29.99}
                    ]
                }
            }
        },
        {
            "name": "Empty JSON",
            "payload": {
                "message": "What can you tell me?",
                "json_data": {}
            }
        }
    ]

    print("Testing /api/chat/with-json endpoint")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 60)

        response = client.post(
            "/api/chat/with-json",
            json=test_case["payload"],
            headers={"Content-Type": "application/json"}
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.get_json()
            print("Success!")
            if result.get("numeric_summary"):
                print(f"Numeric Summary:\n{result['numeric_summary']}")
        elif response.status_code == 401:
            print("Authentication required (expected - endpoint is protected)")
        else:
            result = response.get_json()
            print(f"Failed: {result}")

    print("\n" + "=" * 60)
    print("Tests completed!")

if __name__ == "__main__":
    test_json_endpoint()
