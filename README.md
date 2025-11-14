# CrisisMesh AI

CrisisMesh AI is an AI-powered, self-healing mesh network that restores connectivity after disasters by turning commodity devices (like Raspberry Pis and smartphones) into intelligent relay nodes.

This repository contains a **Beginner MVP**:

- A 3-node Raspberry Pi mesh network using BATMAN-Adv
- A Python daemon that monitors mesh links and predicts failures with a Random Forest model
- A Flask API that exposes topology and predictions
- A simple TCP chat server for messaging over the mesh
- A React Native chat client
- A Streamlit dashboard to visualize topology and failure probabilities

> This MVP is designed so a single student can build it in ~2–3 weeks.

---

## Architecture (MVP)

**Data plane**

- Linux + BATMAN-Adv kernel module for layer-2 mesh routing
- Raspberry Pi nodes on the same Wi-Fi mesh network

**Control plane**

- `mesh_monitor.py` reads BATMAN originators table
- Extracts link features and logs them
- Trained Random Forest model predicts failure probability for each neighbor
- Optional route actions via `batctl` (can be enabled later)

**APIs**

- `api.py` (Flask) exposes:
  - `GET /api/v1/topology`
  - `GET /api/v1/predictions`

**Apps**

- `chat_server.py`: basic TCP relay server running on one Pi
- `mobile/App.js`: React Native chat client that connects over mesh IP
- `dashboard/dashboard.py`: Streamlit dashboard showing neighbors and failure probabilities

---

## Quickstart (High Level)

### 1. Raspberry Pi Setup

- Use at least 3x Raspberry Pi 4 (or similar)
- Install Raspberry Pi OS Lite (64-bit) on each
- Connect them to the same Wi-Fi / ad-hoc network
- Enable SSH on all
- Install BATMAN-Adv and Python dependencies

### 2. Backend

On each Pi:

```bash
sudo apt update
sudo apt install -y batctl python3-pip

# Clone repo
git clone <your-repo-url> crisismesh-ai
cd crisismesh-ai/backend

pip3 install -r requirements.txt
