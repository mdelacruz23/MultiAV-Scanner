import os
import socket

# This file houses all default settings for the Kafka consumer information
KAFKA_HOSTS = ['localhost:9092']
KAFKA_PORT = '9092'
KAFKA_GROUP = 'ffs_mvs_'
KAFKA_CONSUMER_AUTO_OFFSET_RESET = 'latest'
KAFKA_CONSUMER_AUTO_COMMIT_ENABLE = False
KAFKA_PRODUCER_BATCH_LINGER_MS = 25  # 25 ms before flush
KAFKA_PRODUCER_BUFFER_BYTES = 4 * 1024 * 1024  # 4MB before blocking


class Config(object):

    # bootstrap_server = os.getenv('BOOTSTRAP_SERVER', KAFKA_HOSTS)
    bootstrap_server = os.environ['BOOTSTRAP_SERVER']
    consumer_topic = os.environ['KAFKA_CONSUMER_TOPIC']
    producer_topic = os.environ['KAFKA_PRODUCER_TOPIC']
    infected_path = os.getenv("FS_INFECTED_PATH", "/var/scan/infected")
    input_path = os.getenv("FS_INPUT_DIR_PATH", "/var/scan/input")
    output_path = os.getenv("FS_OUTPUT_DIR_PATH", "/var/scan/output")
    group_id = KAFKA_GROUP + socket.gethostbyaddr(socket.gethostname())[0]
    enable_auto_commit = KAFKA_CONSUMER_AUTO_COMMIT_ENABLE
    auto_offset_reset = KAFKA_CONSUMER_AUTO_OFFSET_RESET
    prefix = '/tmp/fs_scan/virus_scan'
    buffer_memory = KAFKA_PRODUCER_BUFFER_BYTES
    kafka_port = KAFKA_PORT
