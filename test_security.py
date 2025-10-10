#!/usr/bin/env python3
"""
Script to test security features of the chatbot API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_security_headers():
    """Test security headers are present"""
    print("\n=== Testing Security Headers ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")

    # Check for security headers
    headers_to_check = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Content-Security-Policy"
    ]

    print("\nSecurity Headers:")
    for header in headers_to_check:
        value = response.headers.get(header, "NOT FOUND")
        print(f"  {header}: {value}")

    return response


def test_input_validation():
    """Test input validation and sanitization"""
    print("\n=== Testing Input Validation ===")

    # Test empty message
    print("\n1. Empty message:")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "   "}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response text: {response.text}")

    # Test invalid session ID
    print("\n2. Invalid session ID format:")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "Hello!",
            "session_id": "invalid-uuid-format"
        }
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response text: {response.text}")

    # Test very long message
    print("\n3. Very long message (>1000 chars):")
    long_message = "A" * 1001
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": long_message}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response text: {response.text}")


def test_rate_limiting():
    """Test rate limiting (10 requests per minute)"""
    print("\n=== Testing Rate Limiting ===")
    print("Sending 12 requests rapidly (limit is 10/minute)...")

    successful = 0
    rate_limited = 0

    for i in range(12):
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": f"Test message {i+1}"}
        )

        if response.status_code == 200:
            successful += 1
            print(f"  Request {i+1}: ✓ Success")
        elif response.status_code == 429:
            rate_limited += 1
            print(f"  Request {i+1}: ✗ Rate limited")
            print(f"    Headers: {dict(response.headers)}")
            break
        else:
            print(f"  Request {i+1}: ? Status {response.status_code}")

        time.sleep(0.1)  # Small delay between requests

    print(f"\nResults: {successful} successful, {rate_limited} rate-limited")
    return successful, rate_limited


def test_budget_status():
    """Test budget status endpoint"""
    print("\n=== Testing Budget Status Endpoint ===")
    response = requests.get(f"{BASE_URL}/api/budget/status")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        budget = response.json()
        print("\nBudget Status:")
        print(f"  Today's cost: ${budget['today_cost_usd']:.4f}")
        print(f"  Daily limit: ${budget['daily_cost_limit_usd']:.2f}")
        print(f"  Remaining: ${budget['cost_remaining_usd']:.2f}")
        print(f"  Utilization: {budget['cost_utilization_percent']:.1f}%")
        print(f"  Today's requests: {budget['today_requests']}")
        print(f"  Request limit: {budget['daily_request_limit']}")
    else:
        print(f"Error: {response.json()}")

    return response


def test_normal_chat():
    """Test normal chat functionality"""
    print("\n=== Testing Normal Chat ===")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": "Hello, how are you?"}
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Session ID: {data['session_id']}")
        print(f"Intent: {data['intent']}")
        print(f"Response: {data['message'][:100]}...")
        print(f"Tokens: {data['tokens_used']}, Cost: ${data['cost_usd']:.4f}")
    else:
        print(f"Error: {response.json()}")

    return response


if __name__ == "__main__":
    print("=" * 60)
    print("Portfolio Chatbot API - Security Tests")
    print("=" * 60)

    try:
        # Test 1: Security Headers
        test_security_headers()

        # Test 2: Input Validation
        test_input_validation()

        # Test 3: Normal Chat (before rate limiting)
        test_normal_chat()

        # Test 4: Budget Status
        test_budget_status()

        # Test 5: Rate Limiting (this may fail if too many requests already made)
        print("\n⚠️  Rate limiting test may trigger 429 errors - this is expected!")
        test_rate_limiting()

        print("\n" + "=" * 60)
        print("✅ Security tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API. Is the server running on port 8000?")
    except Exception as e:
        print(f"\n❌ Error: {e}")
