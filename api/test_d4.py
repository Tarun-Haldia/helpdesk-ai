# api/test_d4.py — test Gemini integration
from retriever import load_embedder, retrieve_similar, format_context_for_gemini
from gemini import generate_solution, generate_escalation_message

print("Loading embedder...")
embedder = load_embedder()
print("Embedder loaded.\n")

# ── Test 1: Full pipeline — query → retrieve → generate ──
print("=" * 55)
print("TEST 1: Full solution generation")
print("=" * 55)

query   = "My WiFi is connected but I cannot browse any websites"
intent  = "internet_issue"



similar = retrieve_similar(query, embedder, top_k=3)
context = format_context_for_gemini(similar)
solution = generate_solution(query, intent, context)

print(f"Query   : {query}")
print(f"Intent  : {intent}")
print(f"\nAI Solution:\n{solution}")

# ── Test 2: VPN issue ──
print("\n" + "=" * 55)
print("TEST 2: VPN solution generation")
print("=" * 55)

query2   = "VPN keeps disconnecting and authentication fails every time"
intent2  = "vpn_setup"

similar2  = retrieve_similar(query2, embedder, top_k=3)
context2  = format_context_for_gemini(similar2)
solution2 = generate_solution(query2, intent2, context2)

print(f"Query   : {query2}")
print(f"Intent  : {intent2}")
print(f"\nAI Solution:\n{solution2}")

# ── Test 3: Escalation message ──
print("\n" + "=" * 55)
print("TEST 3: Escalation message (low confidence)")
print("=" * 55)

esc_msg = generate_escalation_message(
    user_query        = "Something is wrong with my computer I don't know what",
    predicted_intent  = "hardware_issue",
    confidence        = 42.5
)
print(f"Escalation message:\n{esc_msg}")

print("\nD4 Gemini test passed.")
