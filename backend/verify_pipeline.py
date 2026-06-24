import os
import json
import asyncio
from app.services.email_parser import EmailParser
from app.services.header_analyzer import HeaderAnalyzer
from app.services.url_analyzer import URLAnalyzer
from app.services.attachment_analyzer import AttachmentAnalyzer
from app.services.threat_intel.manager import ThreatIntelManager
from app.ml.llm_engine import LLMEngine
from app.ml.risk_engine import RiskScoringEngine
from dataclasses import asdict

base_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(base_dir, "tests", "benchmark", "dataset")

async def verify_pipeline():
    phishing_file = os.path.join(dataset_dir, "phishing", "real_0.eml") # We will pick the first real phishing
    benign_file = os.path.join(dataset_dir, "benign", "real_0.eml")     # and first real benign
    
    # Just list to find real ones
    from glob import glob
    phishing_files = glob(os.path.join(dataset_dir, "phishing", "real_*.eml"))
    benign_files = glob(os.path.join(dataset_dir, "benign", "real_*.eml"))
    
    if not phishing_files or not benign_files:
        print("Dataset missing.")
        return
        
    for label, filepath in [("Benign", benign_files[0]), ("Phishing", phishing_files[0])]:
        print(f"\n{'='*50}\nAnalyzing {label} Sample: {os.path.basename(filepath)}\n{'='*50}")
        
        parser = EmailParser()
        with open(filepath, "rb") as f:
            parsed_obj = parser.parse_eml(f.read())
        parsed = asdict(parsed_obj)
        
        header_analyzer = HeaderAnalyzer()
        url_analyzer = URLAnalyzer()
        att_analyzer = AttachmentAnalyzer()
        ti_manager = ThreatIntelManager()
        llm = LLMEngine()
        risk_engine = RiskScoringEngine()
        
        print(f"Extracted URLs: {parsed.get('urls')}")
        
        # Run sync parts
        def run_sync():
            return (
                header_analyzer.analyze(parsed),
                url_analyzer.analyze(parsed.get("urls", [])),
                att_analyzer.analyze(parsed.get("attachments", []))
            )
        h_res, u_res, a_res = await asyncio.to_thread(run_sync)
        
        print(f"URL Score output: {u_res}")
        
        ti_res = await ti_manager.analyze_iocs(parsed.get("iocs", []))
        ai_res = await llm.analyze(parsed, ti_res)
        
        risk = risk_engine.score(h_res, u_res, a_res, ti_res, ai_res)
        
        print("\n--- AI Engine Output ---")
        print(json.dumps(ai_res, indent=2))
        
        print("\n--- Overall Risk Scoring ---")
        print(json.dumps(risk, indent=2))
        
        # Write to file
        with open(f"results_{label}.json", "w") as f:
            json.dump({"ai_analysis": ai_res, "risk_scoring": risk}, f, indent=2)

if __name__ == "__main__":
    asyncio.run(verify_pipeline())
