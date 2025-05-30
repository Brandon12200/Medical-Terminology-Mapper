#!/usr/bin/env python
"""Test if API can start up successfully."""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing API imports...")
    from api.main import app
    print("✓ API imports successful")
    
    print("\nTesting FastAPI app...")
    print(f"✓ App title: {app.title}")
    print(f"✓ App version: {app.version}")
    
    print("\nTesting routers...")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"✓ Route: {route.path}")
    
    print("\nAPI startup test passed! You can now run: python run_api.py")
    
except Exception as e:
    print(f"✗ API startup test failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)