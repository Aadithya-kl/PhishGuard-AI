import requests
import json

print("--- PART 5: CAMPAIGN CLUSTERING AUDIT ---")
url = "http://localhost:8000/api/v1/threat-hunting/campaigns"
r = requests.get(url)
if r.status_code == 200:
    data = r.json()
    print(f"Total Campaigns: {data['total_campaigns']}")
    for campaign in data['campaigns']:
        print(f"\nCampaign: {campaign['name']}")
        print(f"Confidence: {campaign['confidence']}")
        print(f"Total Scans: {campaign['affected_scans_count']}")
        print(f"Shared Indicators: {campaign['shared_indicators']}")
        print(json.dumps(campaign, indent=2))
else:
    print("Failed to fetch campaigns:", r.text)

