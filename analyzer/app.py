import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import json
import yaml
import logging.config
from pykafka import KafkaClient
import os

# Load logging configuration
with open("/app/config/analyzer_log_conf.yaml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

# Create logger
logger = logging.getLogger('basicLogger')

# Log startup message
logger.info("Analyzer service is starting...")

# Load Kafka configurations
with open("/app/config/analyzer_app_conf.yaml", "r") as f:
    config = yaml.safe_load(f.read())

hostname = f"{config['events']['hostname']}:{config['events']['port']}"
topic_name = config['events']['topic']


def get_event(index, event_type):
    logger.info(f"Fetching event of type '{event_type}' at index {index}")
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(topic_name)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    event_counter = 0
    for msg in consumer:
        message = json.loads(msg.value.decode("utf-8"))
        if message["type"] == event_type:
            if event_counter == index:
                response = {
                    "index": index,
                    "event_type": event_type,
                    "payload": message["payload"]
                }
                logger.info(f"Found event at index {index}: {response}")
                return response, 200
            event_counter += 1

    logger.warning(f"No {event_type} event found at index {index}")
    return {"message": f"No {event_type} event at index {index}!"}, 404


def get_event1(index):
    return get_event(index, "part_purchased")


def get_event2(index):
    return get_event(index, "part_delivery")


def get_stats():
    logger.info("Fetching event statistics")
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(topic_name)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    num_event1 = 0
    num_event2 = 0

    for msg in consumer:
        message = json.loads(msg.value.decode("utf-8"))
        if message["type"] == "part_purchased":
            num_event1 += 1
        elif message["type"] == "part_delivery":
            num_event2 += 1

    stats = {"num_event1": num_event1, "num_event2": num_event2}
    logger.info(f"Event statistics: {stats}")
    return stats, 200

def get_event_counts():
    logger.info("Fetching event counts for Consistency Check")
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(topic_name)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    part_purchased_count = 0
    part_delivery_count = 0

    for msg in consumer:
        message = json.loads(msg.value.decode("utf-8"))
        if message["type"] == "part_purchased":
            part_purchased_count += 1
        elif message["type"] == "part_delivery":
            part_delivery_count += 1

    counts = {
        "part_purchased": part_purchased_count,
        "part_delivery": part_delivery_count
    }
    logger.info(f"Event counts: {counts}")
    return counts, 200


def get_event_ids():
    logger.info("Fetching event and trace IDs for Consistency Check")
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(topic_name)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    event_list = []

    # Counters for each type
    event_counters = {
        "part_purchased": 0,
        "part_delivery": 0
    }

    for msg in consumer:
        print(msg)
        message = json.loads(msg.value.decode("utf-8"))
        trace_id = message.get("trace_id")
        event_type = message.get("type", "unknown")

        if trace_id is None:
            logger.warning(f"Skipping event with missing trace_id: {message}")
            continue

        # Assign event_id based on event type counter
        event_id = event_counters.get(event_type, 0)
        event_counters[event_type] = event_id + 1

        event_list.append({
            "event_id": event_id,
            "trace_id": trace_id,
            "type": event_type
        })

    logger.info(f"Total valid events returned: {len(event_list)}")
    return event_list, 200


# Create and configure the API
app = connexion.FlaskApp(__name__, specification_dir="")
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_api("api.yaml", strict_validation=True, validate_responses=True)

# Run the application
if __name__ == "__main__":
    logger.info("Starting Flask application on port 8110")
    app.run(port=8110, host="0.0.0.0")
