import os
import time
import json
import requests
from collections import defaultdict

BASE_URL = "http://localhost:8000/api/v1"
headers = {}

def get_token():
    auth_data = {
        "username": "eval_user@company.com",
        "password": "evalpassword123"
    }
    res = requests.post(f"{BASE_URL}/auth/login", data=auth_data)
    if res.status_code == 200:
        return res.json()["access_token"]
    raise Exception(f"Failed to auth: {res.text}")

token = get_token()
headers["Authorization"] = f"Bearer {token}"

def run_eval():
    with open("adversarial_dataset/labels.json", "r") as f:
        labels = json.load(f)
        
    print("Uploading 126 adversarial samples...")
    scan_ids = {}
    
    directories = ["phishing", "benign", "gray"]
    for d in directories:
        for f_name in os.listdir(f"adversarial_dataset/{d}"):
            with open(f"adversarial_dataset/{d}/{f_name}", "r") as f:
                content = f.read()
            files = {'file': (f_name, content.encode('utf-8'), 'message/rfc822')}
            res = requests.post(f"{BASE_URL}/scans/upload", files=files, headers=headers)
            if res.status_code == 200:
                scan_ids[f_name] = res.json()["id"]
            else:
                print(f"Failed to upload {f_name}: {res.text}")

    print(f"Uploaded {len(scan_ids)} files. Waiting for processing to complete...")
    
    # Poll until all are done
    results = {}
    pending = set(scan_ids.values())
    
    while pending:
        time.sleep(5)
        done_this_round = set()
        for scan_id in pending:
            res = requests.get(f"{BASE_URL}/scans/{scan_id}", headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data["status"] == "completed":
                    f_name = [k for k, v in scan_ids.items() if v == scan_id][0]
                    results[f_name] = data
                    done_this_round.add(scan_id)
        pending -= done_this_round
        print(f"Remaining to process: {len(pending)}")
        
    print("Processing complete. Calculating metrics...")
    
    global_tp = 0
    global_fp = 0
    global_tn = 0
    global_fn = 0
    
    rule_metrics = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "TN": 0})
    
    confusion_matrix = {"overall": {}, "rules": {}}
    eval_details = []
    
    hybrid_expected_total = 0
    hybrid_detected_total = 0

    for f_name, data in results.items():
        meta = labels[f_name]
        is_phishing = meta["type"] == "phishing"
        is_gray = meta["type"] == "gray"
        is_benign = meta["type"] == "benign"
        
        expected_category = meta.get("expected_category")
        expected_rules = meta.get("expected_rules", [])
        
        detections = data.get("detections", [])
        triggered_rules = [d["category"] for d in detections]
        
        # Track for failure analysis
        eval_details.append({
            "filename": f_name,
            "type": meta["type"],
            "expected_category": expected_category,
            "expected_rules": expected_rules,
            "triggered_rules": triggered_rules,
            "overall_score": data.get("overall_risk_score"),
            "risk_level": data.get("risk_level")
        })
        
        # We don't score gray areas for Precision/Recall, just output them
        if is_gray:
            continue

        if is_phishing:
            if triggered_rules:
                global_tp += 1
            else:
                global_fn += 1
                
            if expected_rules: # Hybrid attack
                hybrid_expected_total += len(expected_rules)
                for er in expected_rules:
                    if er in triggered_rules:
                        hybrid_detected_total += 1
                        rule_metrics[er]["TP"] += 1
                    else:
                        rule_metrics[er]["FN"] += 1
            else:
                # Single category attack
                if expected_category in triggered_rules:
                    rule_metrics[expected_category]["TP"] += 1
                else:
                    rule_metrics[expected_category]["FN"] += 1
                    
        elif is_benign:
            if triggered_rules:
                global_fp += 1
                for tr in triggered_rules:
                    rule_metrics[tr]["FP"] += 1
            else:
                global_tn += 1
                # Add TN to all rules
                for r in rule_metrics:
                    rule_metrics[r]["TN"] += 1

    def safe_div(n, d): return round((n/d) * 100, 2) if d > 0 else 0.0
    
    global_acc = safe_div(global_tp + global_tn, global_tp + global_tn + global_fp + global_fn)
    global_prec = safe_div(global_tp, global_tp + global_fp)
    global_rec = safe_div(global_tp, global_tp + global_fn)
    global_f1 = safe_div(2 * (global_prec * global_rec), (global_prec + global_rec))
    global_fpr = safe_div(global_fp, global_fp + global_tn)
    hybrid_coverage = safe_div(hybrid_detected_total, hybrid_expected_total)
    
    report = {
        "global_metrics": {
            "Accuracy": global_acc,
            "Precision": global_prec,
            "Recall": global_rec,
            "F1": global_f1,
            "False_Positive_Rate": global_fpr,
            "Hybrid_Coverage": hybrid_coverage
        }
    }
    
    confusion_matrix["overall"] = {
        "True_Positives": global_tp,
        "False_Positives": global_fp,
        "True_Negatives": global_tn,
        "False_Negatives": global_fn
    }
    
    rule_performance = {}
    for rule, counts in rule_metrics.items():
        tp = counts["TP"]
        fp = counts["FP"]
        fn = counts["FN"]
        tn = counts["TN"]
        
        prec = safe_div(tp, tp + fp)
        rec = safe_div(tp, tp + fn)
        
        rule_performance[rule] = {
            "Precision": prec,
            "Recall": rec,
            "Trigger_Count": tp + fp,
            "False_Positives": fp,
            "False_Negatives": fn
        }
        
    with open("evaluation_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    with open("confusion_matrix.json", "w") as f:
        json.dump(confusion_matrix, f, indent=4)
        
    with open("rule_performance.json", "w") as f:
        json.dump(rule_performance, f, indent=4)
        
    fns = []
    for item in eval_details:
        if item["type"] == "phishing":
            if item["expected_rules"]:
                missed = [r for r in item["expected_rules"] if r not in item["triggered_rules"]]
                if missed:
                    fns.append({"filename": item["filename"], "expected": item["expected_rules"], "actual": item["triggered_rules"], "missed": missed})
            else:
                if item["expected_category"] not in item["triggered_rules"]:
                    fns.append({"filename": item["filename"], "expected": item["expected_category"], "actual": item["triggered_rules"]})
                    
    fps = [item for item in eval_details if item["type"] == "benign" and len(item["triggered_rules"]) > 0]
    
    with open("top_false_negatives.json", "w") as f:
        json.dump(fns[:10], f, indent=4)
        
    with open("top_false_positives.json", "w") as f:
        json.dump(fps[:10], f, indent=4)
        
    print(f"Global Accuracy: {global_acc}%")
    print(f"Global Precision: {global_prec}%")
    print(f"Global Recall: {global_rec}%")
    print(f"Global FPR: {global_fpr}%")
    print(f"Hybrid Coverage: {hybrid_coverage}%")

if __name__ == "__main__":
    run_eval()
