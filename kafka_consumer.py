from kafka import KafkaConsumer
import json

# Configure consumer
consumer = KafkaConsumer(
    bootstrap_servers=["localhost:9094"],
    auto_offset_reset="earliest",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

# Subscribe to topics
consumer.subscribe(["customers.public.users", "customers.public.orders"])

# Read messages
try:
    for message in consumer:
        print(f"Topic: {message.topic}")
        print(f"Partition: {message.partition}")
        print(f"Offset: {message.offset}")
        print(f"Key: {message.key}")
        print(f"Value: {message.value}")
        print("-" * 50)
except KeyboardInterrupt:
    print("Stopped")
finally:
    consumer.close()
