#!/usr/bin/env python3
"""Test supplement database card display."""

import sys
import os
import django

sys.path.insert(0, '/home/student/dev2_cust1/fitness_ai_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_ai_app.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import SupplementDatabase
import json

# Create test user
user, created = User.objects.get_or_create(
    username='supplement_card_test',
    defaults={'email': 'supptest@test.com'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print("✓ Created test user")
else:
    print("✓ Using existing test user")

client = Client()

# Test 1: Check the endpoint returns supplements
print("\n[TEST 1] Testing /api/supplements/ endpoint...")
response = client.get('/api/supplements/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    supplements = data.get('supplements', [])
    print(f"✓ Returned {len(supplements)} supplements")
    
    if len(supplements) > 0:
        # Show first few items
        for i, supp in enumerate(supplements[:3]):
            print(f"  {i+1}. {supp.get('name')} ({supp.get('supplement_type')})")
    else:
        print("⚠ No supplements in database - populating...")
        from django.core.management import call_command
        call_command('populate_supplements')
        response = client.get('/api/supplements/')
        data = response.json()
        supplements = data.get('supplements', [])
        print(f"✓ Now have {len(supplements)} supplements")
else:
    print(f"✗ Error: {response.status_code}")

# Test 2: Check the nutrition page loads
print("\n[TEST 2] Testing nutrition page loads...")
client.login(username='supplement_card_test', password='testpass123')
response = client.get('/nutrition/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode('utf-8')
    if 'SUPPLEMENT DATABASE' in content:
        print("✓ Supplement Database card is in the page")
    else:
        print("✗ Supplement Database card NOT found in page")
    
    if 'supplementDatabaseList' in content:
        print("✓ Supplement database list element found")
    else:
        print("✗ Supplement database list element NOT found")
    
    if 'loadSupplementDatabase' in content:
        print("✓ loadSupplementDatabase function found in page")
    else:
        print("✗ loadSupplementDatabase function NOT found")
    
    if 'supplement-db-item' in content:
        print("✓ Supplement database item styles found")
    else:
        print("✗ Supplement database item styles NOT found")
else:
    print(f"✗ Error loading nutrition page: {response.status_code}")

# Test 3: Check the data structure
print("\n[TEST 3] Checking supplement data structure...")
response = client.get('/api/supplements/')
if response.status_code == 200:
    data = response.json()
    supplements = data.get('supplements', [])
    
    if len(supplements) > 0:
        first = supplements[0]
        required_fields = ['id', 'name', 'supplement_type', 'dosage', 'unit']
        for field in required_fields:
            if field in first:
                print(f"✓ Field '{field}' present: {first.get(field)}")
            else:
                print(f"✗ Field '{field}' MISSING")
    else:
        print("⚠ No supplements to check structure")

print("\n" + "="*60)
print("✅ SUPPLEMENT DATABASE CARD TESTS COMPLETE")
print("="*60)
