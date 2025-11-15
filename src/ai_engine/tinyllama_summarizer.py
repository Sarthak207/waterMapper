import json
import subprocess
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db

# ---------- CONFIG ----------
CREDENTIALS = "src/data_logger/firebase-credentials.json"
DB_URL = "https://watermarker-4e0e7-default-rtdb.asia-southeast1.firebasedatabase.app/"
SENSOR_NODE = "WaterGuardEdge/sensor_data"
SUMMARY_NODE = "WaterGuardEdge/summaries"

# ---------- Firebase Init ----------
cred = credentials.Certificate(CREDENTIALS)
firebase_admin.initialize_app(cred, {"databaseURL": DB_URL})

# ---------- Fetch last 24h data ----------
def fetch_data(hours=24):
    ref = db.reference(SENSOR_NODE)
    raw = ref.get()
    if not raw:
        return []

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    usable = []

    for key, entry in raw.items():
        try:
            ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            if ts < cutoff:
                continue
            usable.append(entry)
        except:
            pass

    return usable

# ---------- LLM Summarizer ----------
def summarize(data):
    if not data:
        return "No telemetry available for the last 24 hours."

    prompt = (
        "Generate a detailed but concise daily water system summary. "
        "Data fields: distance_cm (water level), flow_lpm (usage), "
        "tds_ppm (water quality). Identify: tank fills, usage patterns, leaks, "
        "water quality warnings, and anomalies.\n\n"
        f"Here is the last 24h data in JSON:\n\n{json.dumps(data, indent=2)}\n\n"
        "Now give the final summary:"
    )

    result = subprocess.run(
        ["ollama", "run", "tinyllama", prompt],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        return f"LLM error: {result.stderr}"

    return result.stdout.strip()

# ---------- Upload summary ----------
def save_summary(summary):
    ref = db.reference(SUMMARY_NODE)
    ref.push({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": summary
    })

# ---------- Main ----------
def run():
    print("Fetching telemetry…")
    data = fetch_data()
    print(f"Fetched {len(data)} records.")

    print("Generating summary with TinyLlama…")
    summary = summarize(data)

    print("\n====== SUMMARY ======")
    print(summary)
    print("=====================")

    save_summary(summary)
    print("Summary saved to Firebase.")

if __name__ == "__main__":
    run()
