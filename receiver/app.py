import connexion
from connexion import NoContent
import uuid
import json
from datetime import datetime
import yaml
import logging.config
from pykafka import KafkaClient

from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

# Load logging configuration
with open("/app/config/receiver_log_conf.yaml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

# Create logger
logger = logging.getLogger('basicLogger')

# Load Kafka configuration
def load_eventstore_config():
    with open("/app/config/receiver_app_conf.yaml", "r") as file:
        config = yaml.safe_load(file)
        logger.debug("Loaded event store configuration: %s", config)
        return config

eventstore_config = load_eventstore_config()

# Function to send event to Kafka
def send_event_to_kafka(event_data):
    """Send event data to Kafka topic"""
    kafka_config = eventstore_config["events"]
    client = KafkaClient(hosts=f"{kafka_config['hostname']}:{kafka_config['port']}")
    topic = client.topics[str.encode(kafka_config["topic"])]

    producer = topic.get_sync_producer()
    msg_str = json.dumps(event_data)
    producer.produce(msg_str.encode("utf-8"))

    logger.info(f"Event {event_data['trace_id']} sent to Kafka")
    return NoContent, 201  # Always return 201 (Created)

# Event handler for part purchased event
def part_purchased(body):
    event_data = {
        "trace_id": str(uuid.uuid4()),
        "type": "part_purchased",
        "timestamp": str(datetime.now()),
        "payload": body
    }

    logger.info(f"Received event part_purchased with trace id {event_data['trace_id']}")
    return send_event_to_kafka(event_data)

# Event handler for part delivery event
def part_delivery(body):
    event_data = {
        "trace_id": str(uuid.uuid4()),
        "type": "part_delivery",
        "timestamp": str(datetime.now()),
        "payload": body  # Store full event payload
    }

    logger.info(f"Received event part_delivery with trace id {event_data['trace_id']}")
    return send_event_to_kafka(event_data)

# Create and configure the API
app = connexion.FlaskApp(__name__, specification_dir="")
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_api("car_store_api.yaml", base_path="/receiver", strict_validation=True, validate_responses=True)

# Run the application
if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")  # Start the application on port 8091