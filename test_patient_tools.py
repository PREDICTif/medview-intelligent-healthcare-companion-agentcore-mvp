#!/usr/bin/env python3
"""
Test script for patient database tools
"""

import sys
import os
sys.path.append('agent')

from patient_tools import lookup_patient_record, get_diabetes_patients_list, search_patients_by_name, get_patient_medication_list

def test_patient_tools():
    """Test all patient database tools"""
    
    print("🧪 Testing Patient Database Tools Integration")
    print("=" * 50)
    
    # Test 1: Get diabetes patients list
    print("\n1️⃣ Testing get_diabetes_patients_list()...")
    try:
        result = get_diabetes_patients_list()
        print("✅ Result:")
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Look up a specific patient
    print("\n2️⃣ Testing lookup_patient_record('MRN001')...")
    try:
        result = lookup_patient_record('MRN001')
        print("✅ Result:")
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Search patients by name
    print("\n3️⃣ Testing search_patients_by_name('John')...")
    try:
        result = search_patients_by_name(first_name='John')
        print("✅ Result:")
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get patient medications
    print("\n4️⃣ Testing get_patient_medication_list('MRN001')...")
    try:
        result = get_patient_medication_list('MRN001')
        print("✅ Result:")
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Patient Database Tools Test Complete!")

if __name__ == "__main__":
    test_patient_tools()