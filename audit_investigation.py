import requests
import json

print("--- PART 3: INVESTIGATION WORKBENCH PROOF ---")
base_url = "http://localhost:8000/api/v1/investigations"

# 1. Create Investigation
inv_res = requests.post(base_url, json={
    "title": "Operation PayPal Verify",
    "description": "Investigating credential harvesting",
    "priority": "Medium",
    "severity": "Medium"
})
inv = inv_res.json()
inv_id = inv["id"]
print("Created Investigation:", inv_id)

# 2. Add Artifacts
requests.post(f"{base_url}/{inv_id}/artifacts", json={"artifact_type": "URL", "artifact_value": "http://paypal-secure.com/login"})
requests.post(f"{base_url}/{inv_id}/artifacts", json={"artifact_type": "Domain", "artifact_value": "paypal-secure.com"})
requests.post(f"{base_url}/{inv_id}/artifacts", json={"artifact_type": "Hash", "artifact_value": "d41d8cd98f00b204e9800998ecf8427e"})

# 3. Add Note
requests.post(f"{base_url}/{inv_id}/notes", json={"content": "Found matching hash in VirusTotal. Upgrading severity.", "status": "Escalated", "priority": "Critical", "severity": "Critical"})

# 4. Change Status
requests.post(f"{base_url}/{inv_id}/notes", json={"content": "Changing status only", "status": "In Progress"})

# 5. Fetch full timeline
data = requests.get(f"{base_url}/{inv_id}").json()
print("\nTimeline Events:")
for evt in data["timeline"]:
    print(f"[{evt['timestamp']}] {evt['type']}: {evt['description']}")
