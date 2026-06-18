# api/test_d5.py — test all endpoints via requests
import requests
import json

BASE = "http://127.0.0.1:8000/api/v1"

# ── Test 1: Health check ──
print("TEST 1: Health check")
r = requests.get(f"{BASE}/health")
print(f"  Status : {r.status_code}")
print(f"  Body   : {r.json()}\n")

# ── Test 2: Query endpoint ──
print("TEST 2: Query — internet issue")
r = requests.post(f"{BASE}/query", json={
    "user_query": "My WiFi is connected but I cannot browse any websites"
})
data = r.json()
print(f"  Status           : {r.status_code}")
print(f"  Intent           : {data.get('predicted_intent')}")
print(f"  Confidence       : {data.get('confidence')}%")
print(f"  Should escalate  : {data.get('should_escalate')}")
print(f"  Similar tickets  : {len(data.get('similar_tickets', []))}")
print(f"  Solution preview : {data.get('ai_solution', '')[:120]}...\n")

# ── Test 3: Create ticket ──
print("TEST 3: Create escalation ticket")
r = requests.post(f"{BASE}/ticket", json={
    "user_query"       : "My screen keeps flickering randomly",
    "predicted_intent" : "hardware_issue",
    "ai_suggestions"   : "Check display drivers",
    "user_details"     : "Started after Windows update"
})
print(f"  Status  : {r.status_code}")
print(f"  Body    : {r.json()}\n")



# ── Test 4: Submit feedback ──
print("TEST 4: Submit feedback")
r = requests.post(f"{BASE}/feedback", json={
    "user_query"       : "WiFi not working",
    "predicted_intent" : "internet_issue",
    "ai_solution"      : "Restart router",
    "is_solved"        : True
})
print(f"  Status : {r.status_code}")
print(f"  Body   : {r.json()}\n")

# ── Test 5: List tickets ──
print("TEST 5: List tickets")
r = requests.get(f"{BASE}/tickets")
data = r.json()
print(f"  Status  : {r.status_code}")
print(f"  Total   : {data.get('total')} tickets\n")

print("D5 all endpoints test complete.")
