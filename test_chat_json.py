#!/usr/bin/env python3
"""Test script to debug the /api/chat/with-json 400 error."""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app import create_app

def test_numeric_summary():
    """Test the numeric summary function directly."""
    app = create_app()

    with app.app_context():
        from backend.app.routes.chat import create_blueprint
        from backend.app.container import ServiceContainer

        services = app.config["services"]

        # Get the blueprint to access internal functions
        # We need to import the module to access _generate_numeric_summary
        import backend.app.routes.chat as chat_module

        # Test cases
        test_data = [
            {"simple": {"value": 10}},
            {"array": [1, 2, 3, 4, 5]},
            {"nested": {"items": [{"price": 10}, {"price": 20}, {"price": 30}]}},
            {"empty_array": []},
            {"mixed": {"a": 1, "b": "string", "c": [5, 10, 15]}},
        ]

        print("Testing _generate_numeric_summary function:\n")
        for i, data in enumerate(test_data, 1):
            print(f"Test {i}: {json.dumps(data)}")
            try:
                # Access the function through the module
                # This is a hack but works for testing
                summary = chat_module._generate_numeric_summary(data)
                print(f"Result: {summary}\n")
            except Exception as e:
                print(f"ERROR: {type(e).__name__}: {e}\n")
                import traceback
                traceback.print_exc()

def test_endpoint():
    """Test the actual endpoint with a simple JSON."""
    app = create_app()
    client = app.test_client()

    test_payload = {
        "message": "What is the sum of all values?",
        "json_data": {
            "items": [
                {"id": 1, "value": 10},
                {"id": 2, "value": 20},
                {"id": 3, "value": 30}
            ]
        }
    }

    print("\n" + "="*60)
    print("Testing /api/chat/with-json endpoint:")
    print("="*60)
    print(f"Payload: {json.dumps(test_payload, indent=2)}\n")

    response = client.post(
        "/api/chat/with-json",
        json=test_payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.get_json()}")

    if response.status_code != 200:
        print("\nERROR DETECTED!")
        print(f"Response data: {response.get_data(as_text=True)}")

if __name__ == "__main__":
    print("Starting diagnostic tests...\n")
    test_numeric_summary()
    test_endpoint()
