# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""
Module for sending messages using Kafka (IT Managed Kafka / AWS MSK).
"""

import json
import logging
import threading

from django.conf import settings

__all__ = (
    "send_kafka_message",
    "post_kafka_message",
)

logger = logging.getLogger(__name__)


class KafkaSenderThread(threading.Thread):
    def __init__(self, key, msg, topic_prefix):
        threading.Thread.__init__(self)
        self.key = key
        self.msg = msg
        self.topic_prefix = topic_prefix

    def run(self):
        from kafka import KafkaProducer

        topic = f"{self.topic_prefix}.{self.key}"
        try:
            producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BROKER_URLS,
                security_protocol='SASL_SSL',
                sasl_mechanism='SCRAM-SHA-512',
                sasl_plain_username=settings.KAFKA_USERNAME,
                sasl_plain_password=settings.KAFKA_PASSWORD,
                ssl_cafile=settings.KAFKA_SSL_CAFILE,
                api_version=settings.KAFKA_API_VERSION,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            )
        except Exception:  # noqa: B902
            logger.exception('kafka: failed to create producer for %s', topic)
            return

        try:
            future = producer.send(topic, value=self.msg)
            future.get(timeout=10)
            logger.info('kafka: sent message to %s: %s', topic, self.msg)
        except Exception:  # noqa: B902
            logger.exception('kafka: failed to send message to %s', topic)
        finally:
            producer.close()


def send_kafka_message(message, key):
    tp_list = settings.KAFKA_TOPIC_PREFIX
    if isinstance(tp_list, str):
        tp_list = [tp_list]

    for topic_prefix in tp_list:
        s = KafkaSenderThread(key, message, topic_prefix)
        s.start()


def post_kafka_message(state, etm, key):
    logger.info('kafka: %s %s', etm, state)
    message = {'scan_id': etm.id, 'scan_state': state}
    send_kafka_message(message, key)
