# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

from tusvc_serdes import TestRest
import os
import json
import logging

class TestPayload(object):
    def __init__(self, tc_num, tc_id, pld, pld_num):
        self.tc_num = tc_num
        self.tc_id = tc_id
        self.pld_num = pld_num
        self.pld = pld

    def __del__(self):
        pass

    def __get_err_hdr(self):
        return "TC #{}: PLD #{}: ".format(self.tc_num, self.pld_num)

    def __pre_process_rest_pld(self, pld_tag):
        err_hdr = self.__get_err_hdr()
        if pld_tag not in self.pld:
            raise RuntimeError(err_hdr + "'{}' NOT found".format(pld_tag))
        if not isinstance(self.pld[pld_tag], dict):
            raise TypeError(err_hdr + "'{}' must be of type 'dict'".format(
                pld_tag))
        if "headers" not in self.pld[pld_tag]:
            raise RuntimeError(err_hdr + "'headers' NOT found in '{}'".format(
                pld_tag))
        TestRest.process_rest_headers(pld_tag, self.pld[pld_tag])
        if "body" not in self.pld[pld_tag]:
            raise RuntimeError(err_hdr + "'body' NOT found in '{}'".format(
                pld_tag))
        TestRest.process_rest_body(pld_tag, self.pld[pld_tag])

    def get_tx_pld(self, tx_type):
        logger = logging.getLogger()

        if tx_type == "None":
            return None

        err_hdr = self.__get_err_hdr()
        if tx_type == "Kafka" or tx_type == "CFKafka":
            if "input" not in self.pld:
                raise RuntimeError(err_hdr + "'input' NOT found")
            if not isinstance(self.pld["input"], str):
                raise TypeError(err_hdr + "'input' must be of type 'str'")
            in_file = os.path.join(self.tc_id, self.pld["input"])
            logger.debug("Loading input payload: '{}'".format(in_file))
            with open(in_file, "r") as in_fh:
                return in_fh.read()
        elif tx_type == "REST":
            self.__pre_process_rest_pld("request")
            if "method" not in self.pld["request"]:
                raise RuntimeError(err_hdr + "'method' NOT found in 'request'")
            if "uri" not in self.pld["request"]:
                raise RuntimeError(err_hdr + "'uri' NOT found in 'request'")
            return self.pld["request"]

    def get_exp_pld(self, tx_type, rx_type):
        logger = logging.getLogger()

        if rx_type == "None" and tx_type != "REST":
            return None

        err_hdr = self.__get_err_hdr()
        if rx_type == "Kafka" or rx_type == "CFKafka":
            if "output" not in self.pld:
                raise RuntimeError(err_hdr + "'output' NOT found")
            if not isinstance(self.pld["output"], str):
                raise TypeError(err_hdr + "'output' must be of type 'str'")
            out_file = os.path.join(self.tc_id, self.pld["output"])
            logger.debug("Loading output payload: '{}'".format(out_file))
            with open(out_file, "r") as out_fh:
                exp_pld = out_fh.read()
                if rx_type == "CFKafka":
                    exp_pld = json.loads(exp_pld)
                return exp_pld
        elif tx_type == "REST":
            self.__pre_process_rest_pld("response")
            if "code" not in self.pld["response"]:
                raise RuntimeError(err_hdr + "'code' NOT found in 'response'")
            return self.pld["response"]

    def get_id(self, tx_type, rx_type):
        if tx_type == "None":
            return "PLD #{}".format(self.pld_num)
        elif tx_type == "REST":
            req = self.pld["request"]
            return "REST REQ #{}: {} {}".format(self.pld_num,
                    req["method"], req["uri"])
        elif rx_type == "None":
            return "PLD #{}".format(self.pld_num)
        else:
            return "Sent {}, Expected {}".format(
                    self.pld["input"], self.pld["output"])

