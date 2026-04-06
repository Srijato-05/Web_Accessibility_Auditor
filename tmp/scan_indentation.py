import os

file_path = r"f:\Projects\Web Accesibility Auditor\src\auditor\application\audit_service.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Scanning {file_path} for indentation anomalies...")
class_started = False
for i, line in enumerate(lines):
    if line.strip().startswith("class AuditService"):
        class_started = True
        print(f"Detected Class Definition at line {i+1}")
        continue
    
    if class_started:
        if line.strip() and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
            print(f"POTENTIAL SCOPE BREAK at line {i+1}: '{line.strip()}'")

print("Scan Complete.")
