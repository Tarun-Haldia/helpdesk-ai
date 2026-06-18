# api/test_d2.py — run this to test classifier
from classifier import load_classifier, predict, should_escalate

print('Loading models from Supabase...')
clf = load_classifier()
print('Models loaded.\n')



# Test 1
result = predict('My WiFi is connected but internet is not working', clf)
print(f"Test 1:")
print(f"  Intent     : {result['intent']}")
print(f"  Confidence : {result['confidence']}%")
print(f"  Clean query: {result['clean_query']}")
escalate, reason = should_escalate(result['confidence'])
print(f"  Escalate   : {escalate}")

# Test 2
result2 = predict('I cannot login to my VPN account', clf)
print(f"\nTest 2:")
print(f"  Intent     : {result2['intent']}")
print(f"  Confidence : {result2['confidence']}%")
print(f"  Escalate   : {should_escalate(result2['confidence'])[0]}")

print('\nD2 classifier test passed.')
