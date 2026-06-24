import os
import re

search_dir = r"c:\Users\loges\cybersecurity\backend"
skip_dirs = {".venv", "venv", "__pycache__", "alembic", ".git"}
patterns = re.compile(r'(mock|placeholder|fake|dummy|sample_data|test_data|hardcoded)', re.IGNORECASE)

print("--- PART 7: MOCK DETECTION ---")
findings = []

for root, dirs, files in os.walk(search_dir):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for file in files:
        if not file.endswith(".py"):
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if patterns.search(line):
                        rel_path = os.path.relpath(filepath, search_dir)
                        findings.append(f"{rel_path}:{i+1}: {line.strip()[:100]}")
        except Exception as e:
            pass

for f in findings:
    print(f)
print(f"\nTotal findings: {len(findings)}")
