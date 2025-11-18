import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
from sklearn.linear_model import LinearRegression

# -------------------
# Firebase Setup
# -------------------
cred = credentials.Certificate("src/data_logger/firebase-credentials.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://watermarker-4e0e7-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# -------------------
# DATA FETCH
# -------------------
def fetch_last_hours(hours=12):
    ref = db.reference("WaterGuardEdge/sensor_data")
    data = ref.get()

    if not data:
        return pd.DataFrame()

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    rows = []
    for key, value in data.items():
        try:
            ts = datetime.fromisoformat(value["timestamp"].replace("Z","+00:00"))
            if ts < cutoff:
                continue
            rows.append({
                "timestamp": ts,
                "distance_cm": value.get("distance_cm", None),
                "flow_lpm": value.get("flow_lpm", None),
                "tds_ppm": value.get("tds_ppm", None),
            })
        except:
            pass

    df = pd.DataFrame(rows)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

# -------------------
# PREDICT TANK EMPTY TIME
# -------------------
def predict_empty_time(df, empty_cm=5):
    if len(df) < 4:
        return "Not enough data to predict."

    df["t"] = (df["timestamp"] - df["timestamp"].iloc[0]).dt.total_seconds()
    X = df[["t"]]
    y = df["distance_cm"]

    model = LinearRegression().fit(X, y)
    slope = model.coef_[0]
    intercept = model.intercept_

    if slope >= 0:
        return "Tank is filling or stable, not emptying."

    t_empty = (empty_cm - intercept) / slope
    secs_remaining = t_empty - df["t"].iloc[-1]

    if secs_remaining < 0:
        return "Prediction: Tank already near empty threshold."

    minutes = secs_remaining / 60
    return f"Tank will reach {empty_cm} cm in approx {minutes:.1f} minutes."

# -------------------
# ANOMALY DETECTION (Simple)
# -------------------
def detect_anomalies(df):
    anomalies = []

    # Sudden jumps in level (sensor error)
    diffs = df["distance_cm"].diff().abs()
    if (diffs > 10).any():
        anomalies.append("Sudden spikes in ultrasonic readings detected.")

    # Emptying too fast
    rate = (df.iloc[-1]["distance_cm"] - df.iloc[0]["distance_cm"]) / \
           ((df.iloc[-1]["timestamp"] - df.iloc[0]["timestamp"]).total_seconds() / 3600)
    if rate < -15:
        anomalies.append("Abnormally fast water usage detected.")

    # No change → sensor frozen
    if df["distance_cm"].nunique() == 1:
        anomalies.append("Ultrasonic sensor seems stuck at one reading.")

    return anomalies

# -------------------
# DAILY STATS
# -------------------
def compute_stats(df):
    return {
        "avg_level": float(df["distance_cm"].mean()),
        "min_level": float(df["distance_cm"].min()),
        "max_level": float(df["distance_cm"].max()),
        "avg_flow": float(df["flow_lpm"].mean() if "flow_lpm" in df else 0),
        "tds_avg": float(df["tds_ppm"].mean() if "tds_ppm" in df else 0),
        "samples": len(df)
    }

# -------------------
# MAIN
# -------------------
def run():
    df = fetch_last_hours(12)

    if df.empty:
        print("No recent data.")
        return None

    prediction = predict_empty_time(df)
    anomalies = detect_anomalies(df)
    stats = compute_stats(df)

    print("\n=== ML PREDICTION ===")
    print(prediction)

    print("\n=== ANOMALIES ===")
    print(anomalies)

    print("\n=== STATS ===")
    print(stats)

    return {
        "prediction": prediction,
        "anomalies": anomalies,
        "stats": stats,
        "raw": df.to_dict(orient="records")
    }

if __name__ == "__main__":
    run()

