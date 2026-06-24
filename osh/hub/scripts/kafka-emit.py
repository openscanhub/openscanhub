#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

import json
import os
import sys

from kafka import KafkaProducer

KAFKA_BROKER_URLS = [
    'b-3.itsandbox.642qp2.c5.kafka.us-east-1.amazonaws.com:9096',
    'b-1.itsandbox.642qp2.c5.kafka.us-east-1.amazonaws.com:9096',
    'b-2.itsandbox.642qp2.c5.kafka.us-east-1.amazonaws.com:9096',
]

KAFKA_TOPIC_PREFIX = 'dev.eng.openscanhub.scan'
KAFKA_USERNAME = 'openscanhub_sandbox'


def main():
    password = os.environ.get('KAFKA_PASSWORD')
    if not password:
        print('Error: KAFKA_PASSWORD environment variable is not set', file=sys.stderr)
        sys.exit(1)

    key = 'unfinished'
    topic = f"{KAFKA_TOPIC_PREFIX}.{key}"
    msg = {'scan_id': 37113, 'scan_state': 'SCANNING'}

    print(f"Connecting to Kafka brokers: {KAFKA_BROKER_URLS}")
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER_URLS,
        security_protocol='SASL_SSL',
        sasl_mechanism='SCRAM-SHA-512',
        sasl_plain_username=KAFKA_USERNAME,
        sasl_plain_password=password,
        ssl_cafile='/etc/pki/tls/certs/ca-bundle.crt',
        api_version=(2, 8, 0),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )

    print(f"Sending message to topic: {topic}")
    print(f"Message: {json.dumps(msg)}")
    future = producer.send(topic, value=msg)

    record_metadata = future.get(timeout=10)
    print("Message sent successfully:")
    print(f"  topic: {record_metadata.topic}")
    print(f"  partition: {record_metadata.partition}")
    print(f"  offset: {record_metadata.offset}")

    producer.close()


if __name__ == "__main__":
    main()
