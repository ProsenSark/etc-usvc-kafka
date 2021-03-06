# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

import six
import avro.schema
import avro.io
import io
import os
import json
import logging

class TestRest(object):
    @staticmethod
    def process_rest_headers(tag, rest):
        try:
            if isinstance(rest["headers"], str):
                rest["headers"] = json.loads(rest["headers"])
            elif not isinstance(rest["headers"], dict):
                rest["headers"] = dict(rest["headers"])
        except Exception as exc:
            raise RuntimeError("Parsing '{}' > 'headers' failed: {}".format(
                tag, exc))

    @staticmethod
    def process_rest_body(tag, rest):
        try:
            if ("Content-Type" in rest["headers"] and
                    rest["headers"]["Content-Type"] == "application/json"):
                rest["body"] = json.loads(rest["body"])
        except Exception as exc:
            pass


class TestSerializer(object):
    def __init__(self, tc_drv, cfg_src_serial, cfg_sink_serial):
        logger = logging.getLogger()

        self.tc_drv = tc_drv
        self.tc_id = tc_drv.get_id()
        self.src = {}
        self.sink = {}
        self.__init_common(cfg_src_serial, self.src)
        self.__init_common(cfg_sink_serial, self.sink)
        if six.PY3:
            f_rmode = "r"
        else:
            f_rmode = "rb"
        if self.src["serialize"] and self.src["type"] == "Avro":
            src_file = os.path.join(self.tc_id, self.src["avro_schema"])
            logger.debug("Loading source Avro: '{}'".format(src_file))
            with open(src_file, f_rmode) as src_fh:
                if six.PY3:
                    schema = avro.schema.Parse(src_fh.read())
                else:
                    schema = avro.schema.parse(src_fh.read())
                self.src["avro_writer"] = avro.io.DatumWriter(schema)
        if self.sink["serialize"] and self.sink["type"] == "Avro":
            sink_file = os.path.join(self.tc_id, self.sink["avro_schema"])
            logger.debug("Loading sink Avro: '{}'".format(sink_file))
            with open(sink_file, f_rmode) as sink_fh:
                if six.PY3:
                    schema = avro.schema.Parse(sink_fh.read())
                else:
                    schema = avro.schema.parse(sink_fh.read())
                self.sink["avro_reader"] = avro.io.DatumReader(schema)

    def __init_common(self, cfg_serial, ep):
        if not cfg_serial:
            raise ValueError("'cfg_serial' is a required parameter")
        if not isinstance(cfg_serial, dict):
            raise TypeError("'serialize' must be of type 'dict'")
        if "enable" not in cfg_serial:
            raise RuntimeError("'enable' NOT found in 'serialize' dict")
        ep["serialize"] = cfg_serial["enable"]
        if ep["serialize"]:
            if "type" not in cfg_serial:
                raise RuntimeError("'type' NOT found in 'serialize' dict")
            ep["type"] = cfg_serial["type"]
            if ep["type"] == "Avro":
                if "avro" not in cfg_serial:
                    raise RuntimeError("'avro' NOT found in 'serialize' dict")
                cfg_avro = cfg_serial["avro"]
                if not isinstance(cfg_avro, dict):
                    raise TypeError("'avro' must be of type 'dict'")
                if "schema" not in cfg_avro:
                    raise RuntimeError("'schema' NOT found in 'avro' dict")
                if not isinstance(cfg_avro["schema"], str):
                    raise TypeError("'schema' must be of type 'str'")
                ep["avro_schema"] = cfg_avro["schema"]
            elif ep["type"] == "Binary":
                pass
            else:
                raise RuntimeError("Unsupported 'type'='%s' in 'serialize' dict" %
                        (cfg_serial["type"]))

    def __del__(self):
        pass

    def serialize(self, test_in):
        logger = logging.getLogger()

        if self.src["serialize"]:
            if not isinstance(test_in, str):
                raise TypeError("'test_in' must be of type 'str'")
            if self.src["type"] == "Avro":
                py_obj = json.loads(test_in)
                bytes_writer = io.BytesIO()
                encoder = avro.io.BinaryEncoder(bytes_writer)
                self.src["avro_writer"].write(py_obj, encoder)
                raw_bytes = bytes_writer.getvalue()
                return raw_bytes
            elif self.src["type"] == "Binary":
                return test_in.encode("utf-8")

        return test_in

    def deserialize(self, test_out, exp_out):
        logger = logging.getLogger()

        if self.sink["serialize"]:
            if not isinstance(exp_out, str):
                raise TypeError("'exp_out' must be of type 'str'")
            if not isinstance(test_out, bytes):
                raise TypeError("'test_out' must be of type 'bytes'")
            if self.sink["type"] == "Avro":
                py_obj = json.loads(exp_out)
                self.tc_drv.store_exp_one(py_obj)

                value = bytearray(test_out)
                bytes_reader = io.BytesIO(value)
                decoder = avro.io.BinaryDecoder(bytes_reader)
                py_obj = self.sink["avro_reader"].read(decoder)
                self.tc_drv.store_rx_one(py_obj)
                return py_obj
            elif self.sink["type"] == "Binary":
                self.tc_drv.store_exp_one(exp_out)

                self.tc_drv.store_rx_one(test_out)
                return test_out.decode("utf-8")
        else:
            self.tc_drv.store_exp_one(exp_out)

        return test_out

