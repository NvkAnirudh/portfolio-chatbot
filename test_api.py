#!/usr/bin/env python3
"""
Simple script to test the chatbot API endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_greeting():
    """Test greeting message"""
    print("\n=== Testing Greeting ===")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "Hello!"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_skills_question(session_id):
    """Test skills question"""
    print("\n=== Testing Skills Question ===")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "What are your Python skills?",
            "session_id": session_id
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_session_history(session_id):
    """Test getting session history"""
    print(f"\n=== Testing Session History for {session_id} ===")
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/history")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total messages: {data['summary']['total_messages']}")
    print(f"Intents: {data['summary']['unique_intents']}")
    return data

if __name__ == "__main__":
    try:
        # Test 1: Greeting (no LLM call)
        result1 = test_greeting()
        session_id = result1["session_id"]

        # Test 2: Skills question (with LLM call)
        result2 = test_skills_question(session_id)

        # Test 3: Get session history
        history = test_session_history(session_id)

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
