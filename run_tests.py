import asyncio
import httpx
import json

API_URL = "http://localhost:8000/api/v1/scans"

async def test_pipeline(filepath, label):
    print(f"\n--- Testing {label} ({filepath}) ---")
    async with httpx.AsyncClient() as client:
        # Upload
        with open(filepath, "rb") as f:
            files = {"file": (filepath, f, "message/rfc822")}
            response = await client.post(f"{API_URL}/upload", files=files)
            
        if response.status_code != 200:
            print(f"Failed to upload: {response.text}")
            return
            
        scan_id = response.json()["id"]
        print(f"Uploaded successfully. Scan ID: {scan_id}")
        
        # Poll for completion
        for _ in range(30):
            await asyncio.sleep(2)
            resp = await client.get(f"{API_URL}/{scan_id}")
            if resp.status_code == 200:
                data = resp.json()
                if data["status"] in ["completed", "failed"]:
                    print(f"Status: {data['status']}")
                    
                    if data["status"] == "completed":
                        print(f"Risk Level: {data.get('risk_level')}")
                        print(f"Overall Score: {data.get('overall_risk_score')}")
                        
                        ai_analysis = data.get('ai_analysis')
                        if ai_analysis:
                            print(f"AI Classification: {ai_analysis.get('attack_classification')}")
                            print(f"AI Severity: {ai_analysis.get('severity_level')}")
                            print(f"AI Reasoning: {ai_analysis.get('reasoning')}")
                            
                        break
        
        # Save output
        with open(f"out_{label}.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"Full results saved to results_{label}.json")

async def main():
    await test_pipeline("test_phishing.eml", "Phishing")
    await test_pipeline("test_benign.eml", "Benign")

if __name__ == "__main__":
    asyncio.run(main())
