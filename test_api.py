import requests

url = "http://localhost:8000/api/v1/investigations"
payload = {
    "title": "BEC Activity",
    "description": "Tracing paypal attacks",
    "priority": "High",
    "severity": "High"
}
response = requests.post(url, json=payload)
print(response.status_code)
print(response.text)
