# MINEGUARD - Phase 1: Data Preparation & Schema Alignment

## Project Structure
```
mineguard/
├── schema/
│   └── incident_schema.py      # Unified JSON schema
├── scripts/
│   ├── build_dataset.py        # Dataset compiler
│   └── iot_streamer.py         # Real-time IoT streamer
├── dataset/
│   └── mining_incidents.csv    # Output (generated)
├── data/
│   ├── dgms_reports/           # DGMS PDFs (downloaded)
│   └── mining_accidents_dataful.csv
└── README.md
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install paho-mqtt pandas PyPDF2 requests
```

### 2. Run Dataset Builder
```bash
cd mineguard
python scripts/build_dataset.py
```

### 3. Run IoT Streamer (separate terminal)
```bash
cd mineguard
python scripts/iot_streamer.py
```

### 4. Expected Output
- `dataset/mining_incidents.csv` - Unified dataset with SIF labels
- MQTT messages published to `mineguard/sensors/Mine_X/all`

## Schema Fields
- incident_id: String identifier
- narrative: Free-text description
- mine_type: Underground / Opencast
- cause_code: DGMS classification
- workplace: Working area
- shift: Relay-1 / Relay-2 / Relay-3 / Night
- worker_type: Departmental / Contractual
- sif_score: Float (0.0-1.0)
- tarp_level: Green / Yellow / Orange / Red
- sif_label: 0 (minor) or 1 (high-fatality)
- hazards: List of extracted hazards
- failed_controls: List of failed safety controls

## Notes
- Schema file defines canonical fields used across DB/backend/frontend
- Dataset builder downloads DGMS PDFs + Dataful CSV, labels SIF, saves unified CSV
- IoT streamer publishes mock sensor data via MQTT (replace with real sensors in production)
