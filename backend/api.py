"""
api.py

Flask API that exposes:

- GET /api/v1/topology
- GET /api/v1/predictions
"""

import time
from typing import Any, Dict, List

import numpy as np
from flask import Flask, jsonify
from flask_cors import CORS

from mesh_monitor import (
    parse_batman_originators,
    estimate_signal_strength,
    estimate_packet_loss,
    get_battery_pct,
    MODEL,
)

app = Flask(__name__)
CORS(app)


@app.route("/api/v1/topology", methods=["GET"])
def topology() -> Any:
    try:
        neighbors = parse_batman_originators()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    nodes: List[Dict[str, Any]] = []
    for n in neighbors:
        nodes.append(
            {
                "neighbor": n["neighbor"],
                "last_seen_ms": n["last_seen_ms"],
                "tq": n["tq"],
                "hop_count": n["hop_count"],
            }
        )

    return jsonify({"timestamp": time.time(), "neighbors": nodes})


@app.route("/api/v1/predictions", methods=["GET"])
def predictions() -> Any:
    if MODEL is None:
        return jsonify({"error": "Model not loaded on this node"}), 500

    try:
        neighbors = parse_batman_originators()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    preds = []
    for n in neighbors:
        signal_strength = estimate_signal_strength(n["tq"])
        packet_loss = estimate_packet_loss(n["tq"])
        hop_count = n["hop_count"]
        battery_pct = get_battery_pct()

        X = np.array([[signal_strength, packet_loss, hop_count, battery_pct]])
        prob = float(MODEL.predict_proba(X)[0, 1])

        preds.append(
            {
                "neighbor": n["neighbor"],
                "failure_prob": prob,
                "tq": n["tq"],
                "hop_count": n["hop_count"],
            }
        )

    return jsonify({"timestamp": time.time(), "predictions": preds})


if __name__ == "__main__":
    # Run on all interfaces so other devices can reach it over the mesh
    app.run(host="0.0.0.0", port=5000)
