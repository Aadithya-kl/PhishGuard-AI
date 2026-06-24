import os
import json
import asyncio
import time
from glob import glob
from app.services.email_parser import EmailParser
from app.services.header_analyzer import HeaderAnalyzer
from app.services.url_analyzer import URLAnalyzer
from app.services.attachment_analyzer import AttachmentAnalyzer
from app.services.threat_intel.manager import ThreatIntelManager
from app.ml.llm_engine import LLMEngine
from app.ml.risk_engine import RiskScoringEngine

base_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(base_dir, "dataset")

from dataclasses import asdict

async def evaluate_email(filepath, expected_label):
    parser = EmailParser()
    with open(filepath, "rb") as f:
        raw_content = f.read()
    parsed_obj = parser.parse_eml(raw_content)
    parsed = asdict(parsed_obj)
    
    header_analyzer = HeaderAnalyzer()
    url_analyzer = URLAnalyzer()
    att_analyzer = AttachmentAnalyzer()
    ti_manager = ThreatIntelManager()
    llm = LLMEngine()
    risk_engine = RiskScoringEngine()
    
    def run_sync_analyzers():
        h_res = header_analyzer.analyze(parsed)
        u_res = url_analyzer.analyze(parsed.get("urls", []))
        a_res = att_analyzer.analyze(parsed.get("attachments", []))
        return h_res, u_res, a_res
        
    header_res, url_res, att_res = await asyncio.to_thread(run_sync_analyzers)
    
    ti_res = await ti_manager.analyze_iocs(parsed.get("iocs", []))
    ai_res = await llm.analyze(parsed, ti_res)
    
    risk = risk_engine.score(header_res, url_res, att_res, ti_res, ai_res)
    
    # "malicious" if risk_level is high or suspicious
    predicted = "phishing" if risk["risk_level"] in ["high", "suspicious"] else "benign"
    
    return {
        "file": os.path.basename(filepath),
        "expected": expected_label,
        "predicted": predicted,
        "risk_level": risk["risk_level"],
        "overall_score": risk["overall_score"],
        "classification": ai_res.get("attack_classification"),
        "reasoning": risk["reasoning"]
    }

async def run_evaluation():
    phishing_files = glob(os.path.join(dataset_dir, "phishing", "*.eml"))
    benign_files = glob(os.path.join(dataset_dir, "benign", "*.eml"))
    
    results = []
    print(f"Evaluating {len(phishing_files)} phishing and {len(benign_files)} benign emails...")
    
    sem = asyncio.Semaphore(5)
    
    async def bounded_evaluate(f, label):
        async with sem:
            return await evaluate_email(f, label)
            
    tasks = [bounded_evaluate(f, "phishing") for f in phishing_files] + \
            [bounded_evaluate(f, "benign") for f in benign_files]
            
    results = await asyncio.gather(*tasks)
        
    # Calculate metrics
    tp = sum(1 for r in results if r["expected"] == "phishing" and r["predicted"] == "phishing")
    fp = sum(1 for r in results if r["expected"] == "benign" and r["predicted"] == "phishing")
    tn = sum(1 for r in results if r["expected"] == "benign" and r["predicted"] == "benign")
    fn = sum(1 for r in results if r["expected"] == "phishing" and r["predicted"] == "benign")
    
    total = len(results)
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0
    
    metrics = {
        "total_samples": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4)
    }
    
    print(json.dumps(metrics, indent=2))
    
    with open("benchmark_results.json", "w") as f:
        json.dump({"metrics": metrics, "detailed_results": results}, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
