import ast
import json
import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# Constants
SINGAPORE_GEF = 0.42
VCPU_POWER_KW = 0.0021

# In-memory storage
global_research_library = []

# Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# Prompt
def build_prompt(code: str) -> str:
    return f"""
AI Service that audits Python code for efficiency and sustainability ...

Return ONLY JSON:

Structure:
{{
  "summary": "2-3 sentence summary",
  "green_score": 0,
  "issues": [
    {{
      "pattern": "short issue name",
      "severity": "high|medium|low",
      "line_hint": "location",
      "fix": "concrete fix",
      "impact": "impact description",
      "estimated_hours_saved": 0.5
    }}
  ],
  "scores": {{
    "loop_efficiency": 0,
    "memory_management": 0,
    "io_efficiency": 0,
    "algorithmic_complexity": 0,
    "resource_cleanup": 0
  }},
  "total_co2_grams_per_run": 0.0,
  "total_vcpu_hours_saved": 0.0,
  "improved_code": "Greener rewritten Python version of the code"
}}

Code:
```python
{code}
"""

def calculate_environmental_impact(hours_saved):
    energy_kwh = hours_saved * VCPU_POWER_KW
    co2_grams = energy_kwh * SINGAPORE_GEF * 1000
    return round(hours_saved, 4), round(co2_grams, 4)

def extract_json_robustly(raw_text):
    """Regex-based extraction to remove markdown fences and prose."""
    try:
        clean = re.sub(r"```(?:json)?", "", raw_text, flags=re.IGNORECASE).strip()
        clean = clean.replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        # If standard cleaning fails, find the first '{' and last '}'
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("AI did not return valid JSON.")

def call_gemini(prompt):
    if not GEMINI_API_KEY:
        raise EnvironmentError("GEMINI_API_KEY is not set.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    if res.status_code != 200:
        raise Exception(f"Gemini API Error: {res.text}")
    return extract_json_robustly(res.json()["candidates"][0]["content"]["parts"][0]["text"])

class GreenAuditEngine(ast.NodeVisitor):
    def __init__(self):
        self.issues = []

    def visit_For(self, node):
        # Detect range(len(...)) anti-pattern
        if isinstance(node.iter, ast.Call):
            if getattr(node.iter.func, "id", "") == "range":
                if any(
                    isinstance(a, ast.Call) and getattr(a.func, "id", "") == "len"
                    for a in node.iter.args
                ):
                    self.issues.append({
                        "pattern": "Inefficient range(len()) loop",
                        "severity": "medium",
                        "line_hint": f"line {node.lineno}",
                        "fix": "Use direct iteration such as 'for item in list:'",
                        "impact": "Reduces CPU cycles.",
                        "estimated_hours_saved": 0.1
                    })

        # Detect repeated computation inside loop
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and getattr(child.func, "id", "") == "sum":
                self.issues.append({
                    "pattern": "Redundant computation inside loop",
                    "severity": "medium",
                    "line_hint": f"line {getattr(child, 'lineno', node.lineno)}",
                    "fix": "Move repeated calculations outside the loop.",
                    "impact": "Avoids repeated computation and reduces CPU usage.",
                    "estimated_hours_saved": 0.2
                })
                break

        self.generic_visit(node)

def ast_fallback(code):
    try:
        tree = ast.parse(code)
        engine = GreenAuditEngine()
        engine.visit(tree)
        issues = engine.issues

        total_hours = sum(i.get("estimated_hours_saved", 0) for i in issues) or 0.01
        h_saved, co2_saved = calculate_environmental_impact(total_hours)

        if issues:
            summary = "AST fallback: AI currently unavailable. Basic checks detected efficiency issues."
            green_score = max(0, 100 - len(issues) * 15)
            improved_code = code
        else:
            summary = "AST fallback: No major Python efficiency issues were detected."
            green_score = 92
            improved_code = ""

        return {
            "summary": summary,
            "green_score": green_score,
            "issues": issues,
            "scores": {
                "loop_efficiency": 70 if issues else 92,
                "memory_management": 70 if issues else 92,
                "io_efficiency": 70 if issues else 90,
                "algorithmic_complexity": 70 if issues else 90,
                "resource_cleanup": 70 if issues else 95
            },
            "total_vcpu_hours_saved": h_saved,
            "total_co2_grams_per_run": co2_saved,
            "improved_code": improved_code
        }

    except Exception:
        return {
            "summary": "AST fallback: the code could not be fully analysed.",
            "green_score": 50,
            "issues": [],
            "scores": {
                "loop_efficiency": 50,
                "memory_management": 50,
                "io_efficiency": 50,
                "algorithmic_complexity": 50,
                "resource_cleanup": 50
            },
            "total_vcpu_hours_saved": 0.01,
            "total_co2_grams_per_run": 0.0088,
            "improved_code": ""
        }

@app.route("/audit", methods=["POST"])
def audit():
    data = request.get_json()
    code = data.get("code", "")
    if not code: return jsonify({"error": "No code"}), 400

    try:
        ast.parse(code) # Syntax check
    except Exception as e:
        return jsonify({"error": f"Syntax Error: {str(e)}"}), 400

    ai_powered = True
    try:
        result = call_gemini(build_prompt(code))
    except Exception as e:
        print(f"AI Failure - check API key, using Fallback: {e}")
        result = ast_fallback(code)
        ai_powered = False

    total_hours = sum(i.get("estimated_hours_saved", 0) for i in result.get("issues", [])) or 0.01
    h_saved, co2_saved = calculate_environmental_impact(total_hours)
    result["total_vcpu_hours_saved"] = h_saved
    result["total_co2_grams_per_run"] = co2_saved

    # 3. Dual-Utility Storage
    global_research_library.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "green_score": result.get("green_score", 0),
        "co2_saved": co2_saved,
        "ai_powered": ai_powered,
        "issue_count": len(result.get("issues", []))
    })

    return jsonify({"report": result, "ai_powered": ai_powered})

@app.route("/library", methods=["GET"])
def get_library():
    return jsonify(global_research_library)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "GreenOps-as-a-Service backend is running.",
        "endpoints": ["/", "/health", "/audit", "/library"]
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "GreenOps-as-a-Service",
        "gemini_key_set": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)