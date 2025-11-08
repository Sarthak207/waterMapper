import json
import paho.mqtt.client as mqtt
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# ---------- Firebase Setup ----------
cred = credentials.Certificate("src/data_logger/firebase-credentials.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://watermarker-4e0e7-default-rtdb.asia-southeast1.firebasedatabase.app"
})

# ---------- MQTT Setup ----------
BROKER = "localhost"
TOPIC = "water/telemetry"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        distance = data.get("distance_cm")
        flow = data.get("flow_lpm")
        tds = data.get("tds_ppm")

        print(f"[DATA] Distance={distance} cm | Flow={flow} L/min | TDS={tds} ppm")

        # ---------- Push to Firebase ----------
        ref = db.reference("WaterGuardEdge/sensor_data")
        ref.push({
            "timestamp": datetime.now().isoformat(),
            "distance_cm": distance,
            "flow_lpm": flow,
            "tds_ppm": tds
        })

    except Exception as e:
        print(f"Error processing message: {e}")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)
    client.loop_forever()
