import requests
import time

url = "http://localhost:8000/api/v1/scans/paste"
payload = {"raw_content": "From: admin@paypal-secure.com\r\nSubject: Account Locked\r\n\r\nPlease verify your account at http://paypal-secure.com/login"}
print("Starting scan...")
res = requests.post(url, data=payload)
scan_id = res.json()["id"]
print(f"Scan ID: {scan_id}")

status_url = f"http://localhost:8000/api/v1/scans/{scan_id}"
while True:
    s_res = requests.get(status_url)
    status = s_res.json()["status"]
    print(f"Status: {status}")
    if status in ("completed", "failed"):
        break
    time.sleep(2)

ioc_url = "http://localhost:8000/api/v1/threat-hunting/ioc/paypal-secure.com"
r_res = requests.get(ioc_url)
print(f"IOC Status: {r_res.status_code}")
if r_res.status_code == 200:
    print(r_res.json()["relationships"])
else:
    print(r_res.text)
