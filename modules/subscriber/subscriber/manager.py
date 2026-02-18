import json
import os
import signal
import sys
import threading
import time
from uuid import uuid4

from .command_listener import CommandListener
from .subscriber import Subscriber
from shared import setup_logging, get_redis_client

LOGGER = setup_logging(__name__)

COMMAND_CHANNEL = "subscription_commands"

GLOBAL_SUBSCRIPTION_KEY = "global:all_subscriptions"

def load_persisted_subscriptions(redis_client, mqtt_subscriber):
    """Load existing subscriptions from Redis on startup."""
    try:
        all_subs = redis_client.hgetall(GLOBAL_SUBSCRIPTION_KEY)
        for topic_bytes, data_bytes in all_subs.items():
            topic = topic_bytes.decode('utf-8')
            data = json.loads(data_bytes.decode('utf-8'))
            save_path = data.get('save_path')
            filters = data.get('filters', {})
            mqtt_subscriber.subscribe(topic, save_path, filters)
            LOGGER.info(f"Restored subscription: {topic}")
    except Exception as e:
        LOGGER.error(f"Failed to load persisted subscriptions: {e}")


def run_manager():

    try:
        _host = os.getenv("GLOBAL_BROKER_HOST")
        _port = int(os.getenv("GLOBAL_BROKER_PORT", 443))
        _uid = os.getenv("GLOBAL_BROKER_USERNAME", "everyone")
        _pwd = os.getenv("GLOBAL_BROKER_PASSWORD", "everyone")
        _protocol = os.getenv("MQTT_PROTOCOL", "websockets")
        _session = os.getenv("MQTT_SESSION_ID", str(uuid4()))

    except Exception as e:
        LOGGER.error(f"Error setting global broker MQTT configuration: {e}")
        raise e

    broker_config = {
        'host': _host,
        'port': _port,
        'uid': _uid,
        'pwd': _pwd,
        'protocol': _protocol,
        'session': _session
    }

    subscriber_id = broker_config.get('host', 'unknown').replace('.', '-')
    health_key = f"subscriber:health:{subscriber_id}"

    if not broker_config.get('host'):
        LOGGER.error("No broker host provided, exiting")
        sys.exit(1)

    mqtt_subscriber = Subscriber(**broker_config)

    redis_listener = CommandListener(
        subscriber=mqtt_subscriber,
        channel=COMMAND_CHANNEL
    )
    redis_client = get_redis_client()

    mqtt_thread = threading.Thread(target=mqtt_subscriber.start, daemon = True)

    shutdown_event = threading.Event()
    def handle_shutdown(signum, frame):
        LOGGER.info("Received shutdown signal, shutting down")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    mqtt_thread.start()
    redis_listener.start()

    # get existing subscriptions from Redis and subscribe
    load_persisted_subscriptions(redis_client, mqtt_subscriber)

    LOGGER.info(f"Subscription manager started for broker: {broker_config.get('host')}")

    try:
        while not shutdown_event.is_set():
            time.sleep(1)
            redis_client.set(health_key, 'alive', ex=60)
            if not mqtt_thread.is_alive():
                LOGGER.critical("MQTT thread died! Shutting down process.")
                break

    except KeyboardInterrupt:
        LOGGER.info("Received keyboard interrupt, shutting down")

    finally:
        LOGGER.info("Shutting down subscription manager")
        redis_listener.stop()
        mqtt_subscriber.stop()
        mqtt_thread.join(timeout=60)
        LOGGER.info("Subscription manager shutdown complete")