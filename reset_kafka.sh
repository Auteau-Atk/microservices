#!/bin/bash

echo "Stopping Kafka and ZooKeeper..."
docker compose down

echo "Removing Kafka and ZooKeeper data..."
rm ./data/kafka/kafka-logs-kafka/meta.properties 

echo "Restarting Kafka and ZooKeeper..."
docker compose up -d

sleep 5

echo "Kafka reset complete. Checking topics..."
sleep 2
docker compose exec kafka kafka-topics.sh --describe --bootstrap-server kafka:9092
