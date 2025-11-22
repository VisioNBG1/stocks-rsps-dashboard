"""
Quick test script to check if the Flask server is working
Run this while the server is running to diagnose issues
"""
import requests
import json

print("Testing Flask Server...")
print("=" * 50)

# Test 1: Check if server is running
try:
    response = requests.get('http://localhost:5000/test', timeout=5)
    print(f"✓ Test endpoint: {response.status_code}")
    print(f"  Response: {response.json()}")
except Exception as e:
    print(f"✗ Cannot connect to server: {e}")
    print("  Make sure the server is running!")
    exit(1)

# Test 2: Check analyze endpoint
print("\n" + "=" * 50)
print("Testing /analyze endpoint (this may take 30-60 seconds)...")
try:
    response = requests.get('http://localhost:5000/analyze', timeout=120)
    print(f"✓ Analyze endpoint: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Success! Received {len(data.get('sectors', []))} sectors")
        for sector in data.get('sectors', [])[:3]:  # Show first 3
            print(f"    - {sector['name']}: avg_z = {sector['avg_z']:.3f} ({len(sector['stocks'])} stocks)")
    else:
        print(f"  ✗ Error: {response.status_code}")
        print(f"  Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("  ✗ Request timed out (server may be processing)")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "=" * 50)
print("Test complete!")
print("\nIf you see errors, check the server terminal window for detailed logs.")

