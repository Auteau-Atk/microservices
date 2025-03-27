import connexion
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import os
import json
import logging.config
import requests
import yaml
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Load logging configuration
with open("/app/config/processing_log_conf.yaml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def load_get_config():
    with open("/app/config/processing_app_conf.yaml", "r") as file:
        config = yaml.safe_load(file)
        logger.debug("Loaded event store configuration: %s", config)
        return config

get_config = load_get_config()

STATS_FILE = get_config["datastore"]["filename"]

DEFAULT_STATS = {
    "latest_timestamp": datetime.utcnow().isoformat(),
    "num_parts_purchased": 0,
    "average_part_price": 0.0,
    "num_part_deliveries": 0,
    "average_days_of_delivery": 0.0
}

def get_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
            stats["latest_timestamp"] = datetime.fromisoformat(stats["latest_timestamp"])
    else:
        # If the file doesn't exist, create it with DEFAULT_STATS
        stats = DEFAULT_STATS
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, default=str)  # Ensure that non-serializable data like datetime is serialized

    return stats, 200

def update_stats():
    logger.info("Periodic processing has started")

    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
    else:
        # If the file doesn't exist, create it with DEFAULT_STATS
        stats = DEFAULT_STATS
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, default=str)  # Ensure that non-serializable data like datetime is serialized

    start_timestamp = stats["latest_timestamp"]
    end_timestamp = datetime.utcnow().isoformat()

    print(stats)

    # Fetch new data
    purchase_url = f"{get_config['eventstores']['get_part_purchased']['url']}start_timestamp={start_timestamp}&end_timestamp={end_timestamp}"
    delivery_url = f"{get_config['eventstores']['get_part_delivery']['url']}start_timestamp={start_timestamp}&end_timestamp={end_timestamp}"

    purchase_resp = requests.get(purchase_url)
    delivery_resp = requests.get(delivery_url)

    purchases = purchase_resp.json() if purchase_resp.status_code == 200 else []
    deliveries = delivery_resp.json() if delivery_resp.status_code == 200 else []

    if purchase_resp.status_code != 200:
        logger.error(f"Failed to retrieve part purchases: {purchase_resp.status_code}")
    if delivery_resp.status_code != 200:
        logger.error(f"Failed to retrieve part deliveries: {delivery_resp.status_code}")

    logger.info(f"Retrieved {len(purchases)} part purchases and {len(deliveries)} part deliveries")

    # Compute new stats
    latest_purchase_time = max((p["date_created"] for p in purchases), default=start_timestamp)
    latest_delivery_time = max((d["date_created"] for d in deliveries), default=start_timestamp)
    latest_timestamp = max(latest_purchase_time, latest_delivery_time)

    total_price = sum(p["price"] for p in purchases) if purchases else 0
    average_part_price = total_price / len(purchases) if purchases else stats["average_part_price"]

    total_delivery_days = sum(d["estimated_days_of_delivery"] for d in deliveries) if deliveries else 0
    average_days_of_delivery = total_delivery_days / len(deliveries) if deliveries else stats[
        "average_days_of_delivery"]

    # Update stats
    stats.update({
        "latest_timestamp": end_timestamp,
        "num_parts_purchased": stats["num_parts_purchased"] + len(purchases),
        "average_part_price": average_part_price,
        "num_part_deliveries": stats["num_part_deliveries"] + len(deliveries),
        "average_days_of_delivery": average_days_of_delivery
    })

    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

    logger.debug(f"Updated stats: {stats}")
    logger.info("Periodic processing has ended")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(update_stats, 'interval', seconds=get_config['scheduler']['interval'])
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_api("car_store_api.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
