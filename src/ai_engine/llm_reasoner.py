import subprocess
import json

def llm_reason(prediction, anomalies, stats, last24h):
    """
    prediction: str  (from ML model)
    anomalies: list[str]
    stats: dict      (average usage, tds, min/max levels)
    last24h: list    (raw telemetry)
    """

    prompt = f"""
You are an AI water-system analyst. Given the following information:

1. **Prediction**
{prediction}

2. **Detected Anomalies**
{json.dumps(anomalies, indent=2)}

3. **Statistical Trends (past 24h)**
{json.dumps(stats, indent=2)}

4. **Raw 24h Sensor Data**
{json.dumps(last24h[-50:], indent=2)}

Analyze all of this and produce:
- a detailed explanation of WHY the prediction makes sense
- possible causes for anomalies
- insights about water consumption patterns
- suggested actions (leak check, pump timing, tank cleaning)
- confidence level (high/medium/low)

Do NOT repeat the data; provide your reasoning like an expert.
"""

    result = subprocess.run(
        ["ollama", "run", "tinyllama", prompt],
        capture_output=True, 
        text=True
    )

    if result.returncode != 0:
        return "[LLM Error] " + result.stderr

    return result.stdout.strip()
