import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

filepath = r"C:\Users\k2ooi\.gemini\antigravity-cli\brain\df857f5e-8ada-4f62-87cc-6239cd29f9d9\.system_generated\steps\769\content.md"

with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f):
        if "TASK-006" in line or "TASK_006" in line or "006" in line:
            print(f"{i+1}: {line.strip()}")
