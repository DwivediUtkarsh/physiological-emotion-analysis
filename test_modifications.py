"""
Test script to verify Phase 2 modifications compile correctly
Tests import statements and basic functionality
"""

import sys
print("\n" + "="*70)
print("PHASE 2 MODIFICATIONS - SYNTAX & IMPORT TEST")
print("="*70 + "\n")

errors = []
successes = []

# Test 1: Check if db_models can be imported
print("1️⃣  Testing db_models imports...")
try:
    from db_models import (
        insert_signals_bulk,
        insert_change_score,
        insert_feature,
        insert_prediction,
        insert_active_prediction,
        insert_video_start,
        clear_active_predictions
    )
    successes.append("✅ db_models imports successfully")
    print("   ✅ All db_models functions imported")
except Exception as e:
    errors.append(f"❌ db_models import failed: {e}")
    print(f"   ❌ Failed: {e}")

# Test 2: Check signals.py syntax
print("\n2️⃣  Testing signals.py syntax...")
try:
    with open('signals.py', 'r') as f:
        code = f.read()
    compile(code, 'signals.py', 'exec')
    successes.append("✅ signals.py syntax valid")
    print("   ✅ Syntax valid")
except SyntaxError as e:
    errors.append(f"❌ signals.py syntax error: {e}")
    print(f"   ❌ Syntax error: {e}")

# Test 3: Check cal_change_point.py syntax  
print("\n3️⃣  Testing cal_change_point.py syntax...")
try:
    with open('cal_change_point.py', 'r') as f:
        code = f.read()
    compile(code, 'cal_change_point.py', 'exec')
    successes.append("✅ cal_change_point.py syntax valid")
    print("   ✅ Syntax valid")
except SyntaxError as e:
    errors.append(f"❌ cal_change_point.py syntax error: {e}")
    print(f"   ❌ Syntax error: {e}")

# Test 4: Check cal_physiological_diff.py syntax
print("\n4️⃣  Testing cal_physiological_diff.py syntax...")
try:
    with open('cal_physiological_diff.py', 'r') as f:
        code = f.read()
    compile(code, 'cal_physiological_diff.py', 'exec')
    successes.append("✅ cal_physiological_diff.py syntax valid")
    print("   ✅ Syntax valid")
except SyntaxError as e:
    errors.append(f"❌ cal_physiological_diff.py syntax error: {e}")
    print(f"   ❌ Syntax error: {e}")

# Test 5: Check model_prediction.py syntax
print("\n5️⃣  Testing model_prediction.py syntax...")
try:
    with open('model_prediction.py', 'r') as f:
        code = f.read()
    compile(code, 'model_prediction.py', 'exec')
    successes.append("✅ model_prediction.py syntax valid")
    print("   ✅ Syntax valid")
except SyntaxError as e:
    errors.append(f"❌ model_prediction.py syntax error: {e}")
    print(f"   ❌ Syntax error: {e}")

# Test 6: Check main.py syntax
print("\n6️⃣  Testing main.py syntax...")
try:
    with open('main.py', 'r') as f:
        code = f.read()
    compile(code, 'main.py', 'exec')
    successes.append("✅ main.py syntax valid")
    print("   ✅ Syntax valid")
except SyntaxError as e:
    errors.append(f"❌ main.py syntax error: {e}")
    print(f"   ❌ Syntax error: {e}")

# Test 7: Check if modified functions exist
print("\n7️⃣  Testing modified function definitions...")
try:
    from cal_physiological_diff import insert_feature_to_db
    successes.append("✅ insert_feature_to_db function exists")
    print("   ✅ insert_feature_to_db() defined")
except Exception as e:
    errors.append(f"❌ insert_feature_to_db not found: {e}")
    print(f"   ❌ Failed: {e}")

# Test 8: Verify MongoDB connection (if available)
print("\n8️⃣  Testing MongoDB connection...")
try:
    from db_config import DatabaseConnection
    conn = DatabaseConnection()
    if conn.connect():
        successes.append("✅ MongoDB connection successful")
        print("   ✅ MongoDB connected")
        conn.close()
    else:
        print("   ⚠️  MongoDB not running (expected if not started)")
except Exception as e:
    print(f"   ⚠️  MongoDB test skipped: {e}")

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"\n✅ Successes: {len(successes)}")
for success in successes:
    print(f"   {success}")

if errors:
    print(f"\n❌ Errors: {len(errors)}")
    for error in errors:
        print(f"   {error}")
    print("\n⚠️  Please fix errors before proceeding.")
    sys.exit(1)
else:
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Phase 2 modifications are syntactically correct")
    print("✅ Ready for end-to-end testing with hardware")

print("\n" + "="*70 + "\n")

