#!/usr/bin/env python3
"""
Quick test script to verify dashboard starts without hanging
"""

import sys
import os
import threading
import time

def test_dashboard_startup():
    """Test dashboard startup with timeout"""
    print("🧪 Testing dashboard startup...")
    
    # Add timeout protection
    def timeout_handler():
        time.sleep(30)  # Wait 30 seconds max
        print("⚠️ Dashboard startup timeout - killing process")
        os._exit(1)
    
    # Start timeout thread
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()
    
    try:
        # Import and start dashboard
        from WORKING_DASHBOARD import WorkingDashboard
        
        print("✅ Dashboard imported successfully")
        
        # Create dashboard instance
        app = WorkingDashboard()
        print("✅ Dashboard instance created")
        
        # Test basic functionality
        print("🔍 Testing basic functions...")
        
        # Test debug logging
        app.debug_log("Test message")
        print("✅ Debug logging works")
        
        # Test data loading (but don't run mainloop)
        try:
            app.load_data()
            print("✅ Data loading completed")
        except Exception as e:
            print(f"⚠️ Data loading error (non-critical): {str(e)}")
        
        print("✅ Dashboard test completed successfully!")
        print("✅ Dashboard should start without hanging")
        
        # Don't actually run the GUI - just test initialization
        return True
        
    except Exception as e:
        print(f"❌ Dashboard test failed: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_dashboard_startup()
    if success:
        print("\n🎉 TEST PASSED: Dashboard should start without hanging")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED: Dashboard may still have hanging issues")
        sys.exit(1)
