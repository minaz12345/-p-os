import urllib.request
import ssl
import json

ctx = ssl._create_unverified_context()
r = urllib.request.urlopen('https://localhost:8443/health', context=ctx)
data = json.loads(r.read())

print('✅ GATEWAY HEALTH CHECK')
print('=' * 50)
print(f"Status: {data['status']}")
print(f"Database: {data['database']}")
print(f"W11 Flags: {'None (HEALTHY)' if not data['w11_flags'] else ', '.join(data['w11_flags'])}")
print(f"Service: {data['service']}")
print(f"Timestamp: {data['timestamp']}")
