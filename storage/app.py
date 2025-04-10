import connexion
from connexion import NoContent
import functools
import os
from datetime import datetime
from db import make_session
from models import PartPurchased, PartDelivery

import yaml
import logging.config
from sqlalchemy import select

from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

import json
import yaml
import logging.config
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
from db import make_session
from models import PartPurchased, PartDelivery

from manage import create_tables, drop_tables

create_tables()

#with open("/app/config/storage_log_conf.yaml", "r") as f:
with open("/app/config/storage_log_conf.yaml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()
    return wrapper

@use_db_session
def get_part_purchased(session, start_timestamp=None, end_timestamp=None):
    if start_timestamp is None and end_timestamp is None:
        return []

    start = datetime.fromisoformat(start_timestamp.rstrip("Z"))
    end = datetime.fromisoformat(end_timestamp.rstrip("Z"))

    statement = (
        select(PartPurchased)
        .where(PartPurchased.date_created >= start)
        .where(PartPurchased.date_created < end)
    )

    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]

    logger.info("Found %d part purchases (start: %s, end: %s)", len(results), start, end)
    return results

@use_db_session
def get_part_delivery(session, start_timestamp=None, end_timestamp=None):
    if start_timestamp is None and end_timestamp is None:
        return []

    start = datetime.fromisoformat(start_timestamp.rstrip("Z"))
    end = datetime.fromisoformat(end_timestamp.rstrip("Z"))

    statement = (
        select(PartDelivery)
        .where(PartDelivery.date_created >= start)
        .where(PartDelivery.date_created < end)
    )

    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]

    logger.info(f"Found {len(results)} part deliveries (start: {start}, end: {end})")
    return results, 200

@use_db_session
def get_event_counts(session):
    part_purchased_count = session.query(PartPurchased).count()
    part_delivery_count = session.query(PartDelivery).count()

    return {
        "part_purchased": part_purchased_count,
        "part_delivery": part_delivery_count
    }, 200

@use_db_session
def get_event_ids(session):
    purchased = session.query(PartPurchased).all()
    delivered = session.query(PartDelivery).all()

    purchased_ids = [
        {"event_id": purchase.part_id, "trace_id": purchase.trace_id, "type": "part_purchased"}
        for purchase in purchased
    ]

    delivery_ids = [
        {"event_id": delivery.delivery_id, "trace_id": delivery.trace_id, "type": "part_delivery"}
        for delivery in delivered
    ]

    return purchased_ids + delivery_ids, 200

# Load Kafka configurations
with open("/app/config/storage_app_conf.yaml", "r") as f:
    config = yaml.safe_load(f.read())

hostname = f"{config['events']['hostname']}:{config['events']['port']}"
topic_name = config['events']['topic']

def process_messages():
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(topic_name)]

    consumer = topic.get_simple_consumer(
        consumer_group=b'event_group',
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST
    )

    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg_json = json.loads(msg_str)

        logger.info(f"Received message: {msg_json}")

        payload = msg_json["payload"]
        session = make_session()

        print(payload)

        if msg_json["type"] == "part_purchased":
            event = PartPurchased(
                trace_id=msg_json['trace_id'],
                part_name=payload['part_name'],
                price=payload['price'],
                seller_id=payload['seller_id'],
                buyer_id=payload['buyer_id'],
                date_created=datetime.utcnow()
            )
            session.add(event)

        elif msg_json["type"] == "part_delivery":
            event = PartDelivery(
                trace_id=msg_json['trace_id'],
                estimated_days_of_delivery=payload['estimated_days_of_delivery'],
                departure_date=datetime.fromisoformat(payload['departure_date']),
                destination=payload['destination'],
                buyer_id=payload['buyer_id'],
                part_id=payload['part_id'],
                date_created=datetime.utcnow()
            )
            session.add(event)

        session.commit()
        consumer.commit_offsets()
        session.close()

def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("car_store_api.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")