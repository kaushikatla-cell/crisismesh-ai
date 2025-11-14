from pathlib import Path

# Path to BATMAN-Adv originators table
BAT_ORIGINATORS_PATH = "/sys/kernel/debug/batman_adv/bat0/originators"

# Logging directory
LOG_DIR = Path("./logs")

# Trained RandomForest model (pickle)
MODEL_PATH = Path("./model/model.pkl")

# Threshold above which we'll consider a link likely to fail
PREDICTION_THRESHOLD = 0.7

# Poll BATMAN table every N seconds
POLL_INTERVAL_SEC = 2

# Perform AI prediction at most every N seconds
PREDICT_INTERVAL_SEC = 5

# Mesh interface name (BATMAN virtual interface)
MESH_INTERFACE = "bat0"
