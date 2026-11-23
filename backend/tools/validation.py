import os
import json
import asyncio
from glob import glob
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

async def run_validation():
    # Only test 5 real benign and 5 real phishing to preserve Gemini API quota
    phishing_files = glob(os.path.join(dataset_dir, "phishing", "real_*.eml"))[:5]
    benign_files = glob(os.path.join(dataset_dir, "benign", "real_*.eml"))[:5]
    
    if len(phishing_files) < 5 or len(benign_files) < 5:
        print("Dataset missing enough real samples. Check dataset generation.")
        return
        
    parser = EmailParser()
    header_analyzer = HeaderAnalyzer()
    url_analyzer = URLAnalyzer()
    att_analyzer = AttachmentAnalyzer()
    ti_manager = ThreatIntelManager()
    llm = LLMEngine()
    risk_engine = RiskScoringEngine()
    
    results = []
    
    print(f"Running Validation on {len(phishing_files)} phishing and {len(benign_files)} benign emails...")
    
    async def evaluate_email(filepath, expected_label):
        with open(filepath, "rb") as f:
            parsed_obj = parser.parse_eml(f.read())
        parsed = asdict(parsed_obj)
        
        def run_sync():
            return (
                header_analyzer.analyze(parsed),
                url_analyzer.analyze(parsed.get("urls", [])),
                att_analyzer.analyze(parsed.get("attachments", []))
            )
        h_res, u_res, a_res = await asyncio.to_thread(run_sync)
        
        ti_res = await ti_manager.analyze_iocs(parsed.get("iocs", []))
        ai_res = await llm.analyze(parsed, ti_res)
        
        risk = risk_engine.score(h_res, u_res, a_res, ti_res, ai_res)
        predicted_label = "phishing" if risk["risk_level"] in ["high", "critical", "suspicious"] else "benign"
        
        return {
            "file": os.path.basename(filepath),
            "expected": expected_label,
            "predicted": predicted_label,
            "ai_analysis": ai_res,
            "risk_scoring": risk
        }

    # Evaluate sequentially to avoid overloading local APIs
    for f in phishing_files:
        res = await evaluate_email(f, "phishing")
        results.append(res)
        
    for f in benign_files:
        res = await evaluate_email(f, "benign")
        results.append(res)
        
    # Metrics Calculation
    tp = sum(1 for r in results if r["expected"] == "phishing" and r["predicted"] == "phishing")
    tn = sum(1 for r in results if r["expected"] == "benign" and r["predicted"] == "benign")
    fp = sum(1 for r in results if r["expected"] == "benign" and r["predicted"] == "phishing")
    fn = sum(1 for r in results if r["expected"] == "phishing" and r["predicted"] == "benign")
    
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn}
    }
    
    # Save the metrics to validation_results.json
    with open("validation_results.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    # Save full dump for proof (first phishing and first benign)
    with open("gemini_proof.json", "w") as f:
        proof = {
            "gemini_execution": results[0]["ai_analysis"],
            "before_after_comparison": {
                "file": results[0]["file"],
                "new_score": results[0]["risk_scoring"]["overall_score"],
                "new_risk_level": results[0]["risk_scoring"]["risk_level"],
                "ai_breakdown": results[0]["risk_scoring"]["breakdown"]
            }
        }
        json.dump(proof, f, indent=2)
        
    print("Validation Complete. Check validation_results.json and gemini_proof.json")

if __name__ == "__main__":
    asyncio.run(run_validation())
