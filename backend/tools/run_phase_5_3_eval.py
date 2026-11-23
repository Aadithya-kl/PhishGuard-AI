import os
import time
import json
import requests
from collections import defaultdict

BASE_URL = "http://localhost:8000/api/v1"
headers = {}

def get_token():
    auth_data = {
        "email": "eval_user@company.com",
        "password": "evalpassword123",
        "full_name": "Eval User"
    }
    requests.post(f"{BASE_URL}/auth/register", json=auth_data)
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": "eval_user@company.com", "password": "evalpassword123"})
    if res.status_code == 200:
        return res.json()["access_token"]
    raise Exception(f"Failed to auth: {res.text}")

token = get_token()
headers["Authorization"] = f"Bearer {token}"

def run_eval():
    with open("benchmark_dataset/labels.json", "r") as f:
        labels = json.load(f)
        
    print("Uploading 100 benchmark samples...")
    scan_ids = {}
    
    # Upload phishing
    for f_name in os.listdir("benchmark_dataset/phishing"):
        with open(f"benchmark_dataset/phishing/{f_name}", "r") as f:
            content = f.read()
        files = {'file': (f_name, content.encode('utf-8'), 'message/rfc822')}
        res = requests.post(f"{BASE_URL}/scans/upload", files=files, headers=headers)
        if res.status_code == 200:
            scan_ids[f_name] = res.json()["id"]
        else:
            print(f"Failed to upload {f_name}: {res.text}")
            
    # Upload benign
    for f_name in os.listdir("benchmark_dataset/benign"):
        with open(f"benchmark_dataset/benign/{f_name}", "r") as f:
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
                    # find the filename
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
    
    category_map = {
        "Business Email Compromise (BEC)": "Business Email Compromise",
        "Credential Harvesting": "Credential Harvesting",
        "Invoice Fraud Attempt": "Invoice Fraud",
        "Malware Delivery": "Malware Delivery",
        "QR Code Phishing (Quishing)": "QR Phishing",
        "OAuth Consent Phishing": "OAuth Consent",
        "MFA Fatigue / Push Spam": "MFA Fatigue",
        "Cryptocurrency Extortion / Scam": "Crypto Scam",
        "Fake Recruiting Campaign": "Fake Recruiting",
        "Brand Impersonation": "Brand Impersonation"
    }
    all_categories = set(category_map[meta["expected_category"]] for meta in labels.values() if meta["expected_category"])
    
    confusion_matrix = {"overall": {}, "rules": {}}
    eval_details = []
    
    for f_name, data in results.items():
        meta = labels[f_name]
        is_phishing = meta["type"] == "phishing"
        expected_category = meta["expected_category"]
        
        # Map expected categories to rule categories
        category_map = {
            "Business Email Compromise (BEC)": "Business Email Compromise",
            "Credential Harvesting": "Credential Harvesting",
            "Invoice Fraud Attempt": "Invoice Fraud",
            "Malware Delivery": "Malware Delivery",
            "QR Code Phishing (Quishing)": "QR Phishing",
            "OAuth Consent Phishing": "OAuth Consent",
            "MFA Fatigue / Push Spam": "MFA Fatigue",
            "Cryptocurrency Extortion / Scam": "Crypto Scam",
            "Fake Recruiting Campaign": "Fake Recruiting",
            "Brand Impersonation": "Brand Impersonation"
        }
        
        expected_category = category_map.get(expected_category) if expected_category else None
        
        detections = data.get("detections", [])
        triggered_rules = [d["category"] for d in detections]
        
        # Global metrics
        if is_phishing:
            if triggered_rules:
                global_tp += 1
            else:
                global_fn += 1
        else:
            if triggered_rules:
                global_fp += 1
            else:
                global_tn += 1
                
        # Rule level metrics
        for cat in all_categories:
            if is_phishing and expected_category == cat:
                if cat in triggered_rules:
                    rule_metrics[cat]["TP"] += 1
                else:
                    rule_metrics[cat]["FN"] += 1
            elif cat in triggered_rules:
                # Rule triggered but it shouldn't have
                rule_metrics[cat]["FP"] += 1
            else:
                rule_metrics[cat]["TN"] += 1
                
        eval_details.append({
            "filename": f_name,
            "type": meta["type"],
            "expected_category": expected_category,
            "triggered_rules": triggered_rules,
            "overall_score": data.get("overall_risk_score")
        })

    # Calculate global percentages
    def safe_div(n, d): return round(n/d * 100, 2) if d > 0 else 0.0
    
    global_acc = safe_div(global_tp + global_tn, 100)
    global_prec = safe_div(global_tp, global_tp + global_fp)
    global_rec = safe_div(global_tp, global_tp + global_fn)
    global_f1 = safe_div(2 * (global_prec * global_rec), (global_prec + global_rec))
    global_fpr = safe_div(global_fp, global_fp + global_tn)
    
    report = {
        "global_metrics": {
            "Accuracy": global_acc,
            "Precision": global_prec,
            "Recall": global_rec,
            "F1": global_f1,
            "False_Positive_Rate": global_fpr,
            "Total_Samples": 100
        },
        "rule_metrics": {}
    }
    
    confusion_matrix["overall"] = {
        "True_Positives": global_tp,
        "False_Positives": global_fp,
        "True_Negatives": global_tn,
        "False_Negatives": global_fn
    }
    
    for rule, counts in rule_metrics.items():
        tp = counts["TP"]
        fp = counts["FP"]
        fn = counts["FN"]
        tn = counts["TN"]
        
        prec = safe_div(tp, tp + fp)
        rec = safe_div(tp, tp + fn)
        f1 = safe_div(2 * (prec * rec), (prec + rec))
        
        report["rule_metrics"][rule] = {
            "Precision": prec,
            "Recall": rec,
            "F1": f1,
            "False_Positives": fp,
            "False_Negatives": fn
        }
        
        confusion_matrix["rules"][rule] = counts

    with open("evaluation_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    with open("confusion_matrix.json", "w") as f:
        json.dump(confusion_matrix, f, indent=4)
        
    fns = [item for item in eval_details if item["type"] == "phishing" and item["expected_category"] not in item["triggered_rules"]]
    fps = [item for item in eval_details if item["type"] == "benign" and len(item["triggered_rules"]) > 0]
    
    with open("eval_errors.json", "w") as f:
        json.dump({"false_negatives": fns, "false_positives": fps}, f, indent=4)
        
    print(f"Global Accuracy: {global_acc}%")
    print(f"Global Precision: {global_prec}%")
    print(f"Global Recall: {global_rec}%")
    print(f"Global FPR: {global_fpr}%")
    print("Done! Generated evaluation_report.json and confusion_matrix.json")

if __name__ == "__main__":
    run_eval()
