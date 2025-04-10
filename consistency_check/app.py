from flask import jsonify
import connexion
from connexion import NoContent
import requests
import json
import time
import os
import yaml
import logging.config
from datetime import datetime

# Load YAML config
with open("/app/config/app_config.yml", "r") as f:
    config = yaml.safe_load(f)

PROCESSING_URL = config["processing_url"]
ANALYZER_URL = config["analyzer_url"]
STORAGE_URL = config["storage_url"]
JSON_FILE = config.get("json_file", "consistency_results.json")
KAFKA_CONFIG = config.get("kafka", {})

# Load logging config
if os.path.exists("/app/config/log_conf.yml"):
    with open("/app/config/log_conf.yml", "r") as f:
        logging_config = yaml.safe_load(f)
        logging.config.dictConfig(logging_config)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def compare_trace_ids(queue_ids, db_ids):
    queue_set = {(e['trace_id'], e['event_id'], e['type']) for e in queue_ids}
    db_set = {(e['trace_id'], e['event_id'], e['type']) for e in db_ids}

    missing_in_db = [
        {"trace_id": trace_id, "event_id": event_id}
        for trace_id, event_id, type_ in queue_set - db_set
    ]
    missing_in_queue = [
        {"trace_id": trace_id, "event_id": event_id}
        for trace_id, event_id, type_ in db_set - queue_set
    ]
    return missing_in_db, missing_in_queue

def run_consistency_checks():
    start_time = time.time()
    logger.info("Consistency check started")

    # Fetch stats and event data
    processing_stats = fetch_json(f"{PROCESSING_URL}/stats")
    queue_stats = fetch_json(f"{ANALYZER_URL}/stats")
    db_stats = fetch_json(f"{STORAGE_URL}/stats")

    queue_ids = fetch_json(f"{ANALYZER_URL}/storage/events")
    db_ids = fetch_json(f"{STORAGE_URL}/ids")

    # Compare IDs
    missing_in_db, missing_in_queue = compare_trace_ids(queue_ids, db_ids)

    # Save result
    result = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "counts": {
            "processing": processing_stats,
            "queue": queue_stats,
            "db": db_stats
        },
        "not_in_db": missing_in_db,
        "not_in_queue": missing_in_queue
    }

    with open(JSON_FILE, 'w') as f:
        json.dump(result, f, indent=2)

    elapsed = int((time.time() - start_time) * 1000)
    logger.info(f"Consistency checks completed | processing_time_ms={elapsed} | "
                f"not_in_db = {len(missing_in_db)} | not_in_queue = {len(missing_in_queue)}")

    return jsonify({"processing_time_ms": elapsed})

def get_checks():
    if not os.path.exists(JSON_FILE):
        return jsonify({"message": "No checks have been run yet."}), 404

    with open(JSON_FILE) as f:
        data = json.load(f)
    return jsonify(data)

# Create and configure the API
app = connexion.FlaskApp(__name__, specification_dir=".")
app.add_api("consistency_check.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8111, host="0.0.0.0")
