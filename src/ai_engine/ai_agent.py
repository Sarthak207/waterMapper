import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Import ML + LLM modules
from analyzer import run as run_analyzer
from llm_reasoner import llm_reason


# -----------------------------------------------------
# Firebase Initialization (SAFE — prevents double init)
# -----------------------------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("src/data_logger/firebase-credentials.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://watermarker-4e0e7-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

SUMMARY_NODE = "WaterGuardEdge/ai_reports"


# -----------------------------------------------------
# Run Full AI Pipeline
# -----------------------------------------------------
def run_ai_pipeline():
    print("\n===================================")
    print("       Running Full AI Pipeline    ")
    print("===================================\n")

    # -----------------------------
    # STEP 1: ML Analyzer
    # -----------------------------
    print("[1] Running ML Analyzer...")
    ml_output = run_analyzer()

    if ml_output is None:
        print("No data available. Cannot continue.")
        return

    prediction = ml_output["prediction"]
    anomalies = ml_output["anomalies"]
    stats = ml_output["stats"]
    raw_data = ml_output["raw"]

    # -----------------------------------------------------
    # FIX: Convert Pandas Timestamp → ISO string
    # -----------------------------------------------------
    for entry in raw_data:
        if "timestamp" in entry and hasattr(entry["timestamp"], "isoformat"):
            entry["timestamp"] = entry["timestamp"].isoformat()

    # -----------------------------
    # STEP 2: LLM Reasoner
    # -----------------------------
    print("\n[2] Running LLM Reasoner (TinyLlama)...")
    final_report = llm_reason(
        prediction=prediction,
        anomalies=anomalies,
        stats=stats,
        last24h=raw_data
    )

    # -----------------------------
    # STEP 3: Upload AI Report
    # -----------------------------
    print("\n[3] Uploading AI Report to Firebase...")
    ref = db.reference(SUMMARY_NODE)
    ref.push({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "prediction": prediction,
        "anomalies": anomalies,
        "stats": stats,
        "ai_report": final_report
    })

    # -----------------------------
    # STEP 4: Print Final Report
    # -----------------------------
    print("\n============== AI REPORT ==============")
    print(final_report)
    print("========================================\n")

    print("AI Pipeline completed successfully.\n")


# -----------------------------------------------------
# MAIN ENTRY
# -----------------------------------------------------
if __name__ == "__main__":
    run_ai_pipeline()

