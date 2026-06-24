import requests
import json

print("--- PART 2: IOC PIVOT ENGINE PROOF ---")
ioc = "paypal-secure.com"
print(f"Pivoting on IOC: {ioc}")

# Hop 1: IOC -> Related URL
ioc_url = f"http://localhost:8000/api/v1/threat-hunting/ioc/{ioc}"
r = requests.get(ioc_url)
if r.status_code == 200:
    data = r.json()
    print("\nHop 1: Pivot via Domain")
    print("Related URLs:", data["relationships"]["related_urls"])
    print("Related Scans:", data["relationships"]["related_scans"])
    print("Related Senders:", data["relationships"]["related_senders"])
    print("Related Campaigns:", data["relationships"]["related_campaigns"])
    print(json.dumps(data, indent=2))
else:
    print("Failed to fetch IOC:", r.text)

