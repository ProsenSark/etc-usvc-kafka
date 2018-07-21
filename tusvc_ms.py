# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

from confluent_kafka import Producer, Consumer
from confluent_kafka import KafkaError
from confluent_kafka import TopicPartition
from confluent_kafka import avro
from confluent_kafka.avro.serializer import SerializerError
import os
import json
import logging

class TestBaseEP(object):
    def __init__(self, cfg):
        if not cfg:
            raise ValueError("'cfg' is a required parameter")
        if self.type == "Kafka":
            cfg_tag = "kafka"
            cfg_kafka = cfg[cfg_tag]
            if not isinstance(cfg_kafka, dict):
                raise TypeError("'{}' must be of type 'dict'".format(cfg_tag))
        elif self.type == "CFKafka":
            cfg_tag = "cfkafka"
            cfg_kafka = cfg[cfg_tag]
            if not isinstance(cfg_kafka, dict):
                raise TypeError("'{}' must be of type 'dict'".format(cfg_tag))
            if "schema.registry" not in cfg_kafka:
                raise RuntimeError("'schema.registry' NOT found in " +
                        "'{}' dict".format(cfg_tag))
            self.schema_reg = cfg_kafka["schema.registry"]

        if "brokers" not in cfg_kafka:
            raise RuntimeError("'brokers' NOT found in " +
                    "'{}' dict".format(cfg_tag))
        if not isinstance(cfg_kafka["brokers"], str):
            raise TypeError("'brokers' must be of type 'str'")
        self.brokers = cfg_kafka["brokers"]
        if "topic" not in cfg_kafka:
            raise RuntimeError("'topic' NOT found in " +
                    "'{}' dict".format(cfg_tag))
        if not isinstance(cfg_kafka["topic"], str):
            raise TypeError("'topic' must be of type 'str'")
        self.topic = cfg_kafka["topic"]

    def __del__(self):
        pass

class TestProducer(TestBaseEP):
    def __init__(self, tc_drv, cfg_src):
        logger = logging.getLogger()

        if not cfg_src:
            raise ValueError("'cfg_src' is a required parameter")
        if "type" not in cfg_src:
            raise RuntimeError("'type' NOT found in 'source' dict")
        self.tc_drv = tc_drv
        self.tc_id = tc_drv.get_id()
        self.type = cfg_src["type"]
        self.prod = None

        if self.type == "Kafka":
            if "kafka" not in cfg_src:
                raise RuntimeError("'kafka' NOT found in 'source' dict")
            super(TestProducer, self).__init__(cfg_src)
        elif self.type == "CFKafka":
            if "cfkafka" not in cfg_src:
                raise RuntimeError("'cfkafka' NOT found in 'source' dict")
            super(TestProducer, self).__init__(cfg_src)

            if "schema.file" not in cfg_src["cfkafka"]:
                raise RuntimeError("'schema.file' NOT found in 'cfkafka' dict")
            self.schema_file = cfg_src["cfkafka"]["schema.file"]
        else:
            raise RuntimeError("Unsupported 'type'='%s' in 'source' dict" %
                    (cfg_src["type"]))

        if not self.prod:
            self.connect()

    def __del__(self):
        self.prod.flush()

    def connect(self):
        logger = logging.getLogger()

        if self.type == "Kafka":
            logger.debug("brokers: {}, topic: {}".format(
                self.brokers, self.topic))
            self.prod = Producer({
                'bootstrap.servers': self.brokers,
                'default.topic.config': {
                    'message.timeout.ms': 30000,
                    #'auto.offset.reset': 'smallest',
                }
            })
        elif self.type == "CFKafka":
            val_schema = avro.load(os.path.join(self.tc_id, self.schema_file))

            logger.debug("brokers: {}, schema_reg: {}, topic: {}".format(
                self.brokers, self.schema_reg, self.topic))
            self.prod = avro.AvroProducer({
                'bootstrap.servers': self.brokers,
                'schema.registry.url': self.schema_reg,
                'default.topic.config': {
                    'message.timeout.ms': 30000,
                    #'auto.offset.reset': 'smallest',
                }
            }, default_value_schema=val_schema)

    def tx_one(self, test_in):
        logger = logging.getLogger()

        if self.type == "Kafka":
            if not isinstance(test_in, bytes):
                raise TypeError("'test_in' must be of type 'bytes'")

            #logger.debug("going to produce")
            self.prod.produce(self.topic, test_in)
            logger.debug("TX'ed '{}' : '{}'".format(type(test_in), test_in))
            #logger.debug("going to poll")
            self.prod.poll(timeout=0.5)
        elif self.type == "CFKafka":
            if not isinstance(test_in, str):
                raise TypeError("'test_in' must be of type 'str'")

            val_obj = json.loads(test_in)
            #logger.debug("going to produce")
            self.prod.produce(topic=self.topic, value=val_obj)
            logger.debug("TX'ed '{}' : '{}'".format(type(val_obj), val_obj))

        #logger.debug("going to flush")
        self.prod.flush()

class TestConsumer(TestBaseEP):
    def __init__(self, tc_drv, cfg_sink):
        logger = logging.getLogger()

        if not cfg_sink:
            raise ValueError("'cfg_sink' is a required parameter")
        if "type" not in cfg_sink:
            raise RuntimeError("'type' NOT found in 'sink' dict")
        self.tc_drv = tc_drv
        self.tc_id = tc_drv.get_id()
        self.type = cfg_sink["type"]
        self.poll_count = 10
        self.cons = None

        if self.type == "Kafka":
            if "kafka" not in cfg_sink:
                raise RuntimeError("'kafka' NOT found in 'sink' dict")
            super(TestConsumer, self).__init__(cfg_sink)

            if "group" not in cfg_sink["kafka"]:
                raise RuntimeError("'group' NOT found in 'kafka' dict")
            if not isinstance(cfg_sink["kafka"]["group"], str):
                raise TypeError("'group' must be of type 'str'")
            self.group = cfg_sink["kafka"]["group"]

            if "timeout" in cfg_sink["kafka"]:
                if not isinstance(cfg_sink["kafka"]["timeout"], int):
                    raise TypeError("'timeout' must be of type 'int'")
                self.poll_count = cfg_sink["kafka"]["timeout"]
        elif self.type == "CFKafka":
            if "cfkafka" not in cfg_sink:
                raise RuntimeError("'cfkafka' NOT found in 'sink' dict")
            super(TestConsumer, self).__init__(cfg_sink)

            if "group" not in cfg_sink["cfkafka"]:
                raise RuntimeError("'group' NOT found in 'cfkafka' dict")
            if not isinstance(cfg_sink["cfkafka"]["group"], str):
                raise TypeError("'group' must be of type 'str'")
            self.group = cfg_sink["cfkafka"]["group"]

            if "timeout" in cfg_sink["cfkafka"]:
                if not isinstance(cfg_sink["cfkafka"]["timeout"], int):
                    raise TypeError("'timeout' must be of type 'int'")
            self.poll_count = cfg_sink["cfkafka"]["timeout"]
        else:
            raise RuntimeError("Unsupported 'type'='%s' in 'sink' dict" %
                    (cfg_sink["type"]))

        if not self.cons:
            self.connect()

    def __del__(self):
        logger = logging.getLogger()

        if self.cons:
            #self.cons.unsubscribe()
            self.cons.close()

    def connect(self):
        logger = logging.getLogger()

        if self.type == "Kafka":
            logger.debug("brokers: {}, group: {}, topic: {}".format(
                self.brokers, self.group, self.topic))
            self.cons = Consumer({
                'bootstrap.servers': self.brokers,
                'group.id': self.group,
                'default.topic.config': {
                    'auto.offset.reset': 'smallest',
                }
            })

            self.cons.subscribe([self.topic])
        elif self.type == "CFKafka":
            logger.debug("brokers: {}, schema_reg: {}, group: {}, topic: {}".format(
                self.brokers, self.schema_reg, self.group, self.topic))
            self.cons = avro.AvroConsumer({
                'bootstrap.servers': self.brokers,
                'schema.registry.url': self.schema_reg,
                'group.id': self.group,
                'default.topic.config': {
                    'auto.offset.reset': 'smallest',
                }
            })

            self.cons.subscribe([self.topic])

    def __reset_pos(self):
        logger = logging.getLogger()

        parts = [TopicPartition(self.topic, 0)]
        (start, end) = self.cons.get_watermark_offsets(parts[0])
        logger.debug("Currently at {}/{} offset <{}, {}>".format(parts[0].topic,
            parts[0].partition, start, end))
        if end > 0:
            parts[0].offset = end - 1
            self.cons.seek(parts[0])

    def rx_one(self, exp_out):
        logger = logging.getLogger()

        logger.warning("will timeout in {} secs".format(self.poll_count))
        #logger.debug("going to consume/poll")
        #msgs = self.cons.consume(num_messages=1, timeout=5.0)
        #if not msgs:
        #    raise RuntimeError("No msg received, timed-out!")
        poll_num = 0
        while True:
            try:
                poll_num += 1
                msg = self.cons.poll(timeout=1.0)
            except SerializerError as exc:
                raise RuntimeError("Message deserialization failed for {}: {}".format(
                    msg, exc))
                break

            if msg is None:
                #parts = self.cons.position(parts)
                #logger.debug("Currently at {}/{} offset {}".format(parts[0].topic,
                #    parts[0].partition, parts[0].offset))
                if poll_num < self.poll_count:
                    continue
                else:
                    raise RuntimeError("No msg received via {}, timed-out!".format(
                        self.topic))
            elif not msg.error():
                break
            elif msg.error().code() == KafkaError._PARTITION_EOF:
                #raise RuntimeError("End of partition reached {}/{}".format(
                #    msg.topic(), msg.partition()))
                #self.__reset_pos()
                #break
                continue
            else:
                raise RuntimeError(msg.error().str())

        test_out = msg.value()
        logger.debug("RX'ed '{}' : '{}'".format(type(test_out), test_out))
        if self.type == "CFKafka":
            self.tc_drv.store_rx_one(test_out)
            if not isinstance(exp_out, str):
                raise TypeError("'exp_out' must be of type 'str'")
            val_obj = json.loads(exp_out)
            self.tc_drv.store_exp_one(val_obj)

        return test_out

