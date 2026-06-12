# api/test_d3.py — test retriever
from retriever import load_embedder, retrieve_similar, format_context_for_gemini

print("Loading embedder...")
embedder = load_embedder()
print("Embedder loaded.\n")

# Test 1 — internet issue
q1      = "My WiFi is connected but I cannot browse any websites"
results = retrieve_similar(q1, embedder, top_k=3)

print(f"Query: {q1}")
print(f"Top {len(results)} similar tickets:")
for r in results:
    print(f"  [{r['similarity']:.3f}] {r['intent']:<28} | {r['user_query'][:55]}")

# Test 2 — VPN issue
print()
q2      = "VPN keeps disconnecting and authentication fails"
results2 = retrieve_similar(q2, embedder, top_k=3)

print(f"Query: {q2}")
print(f"Top {len(results2)} similar tickets:")
for r in results2:
    print(f"  [{r['similarity']:.3f}] {r['intent']:<28} | {r['user_query'][:55]}")

# Test 3 — Gemini context format
print()
print("=== Gemini context format preview ===")
context = format_context_for_gemini(results2)
print(context)

print("D3 retriever test passed.")