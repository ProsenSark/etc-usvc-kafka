# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

import json
import logging

class TestCompare(object):
    @staticmethod
    def compare_py_objs(rx_obj, exp_obj):
        logger = logging.getLogger()

        if isinstance(rx_obj, unicode):
            rx_obj = rx_obj.encode()
        if isinstance(exp_obj, unicode):
            exp_obj = exp_obj.encode()

        if not type(rx_obj) == type(exp_obj):
            #logger.debug("{} vs. {}".format(type(rx_obj), type(exp_obj)))
            return False

        if isinstance(exp_obj, dict):
            for key in exp_obj.keys():
                if not key in rx_obj:
                    return False
                if not TestCompare.compare_py_objs(rx_obj[key], exp_obj[key]):
                    return False
        elif isinstance(exp_obj, list) or isinstance(exp_obj, tuple):
            for exp_mbr in exp_obj:
                found = False
                for rx_mbr in rx_obj:
                    if TestCompare.compare_py_objs(rx_mbr, exp_mbr):
                        found = True
                        break
                if not found:
                    return False
        else:
            return rx_obj == exp_obj

        return True


class TestCaseDriver(object):
    def __init__(self):
        self.tc_id = None
        self.results = {}
        self.num_tcs = 0;
        self.num_plds = 0;
        self.results["testcases"] = []
        self.results["num_oks"] = 0
        self.results["num_noks"] = 0

    def __del__(self):
        pass

    def reinit(self, tc_id):
        self.tc_id = tc_id
        self.num_plds = 0;
        self.rx_pld = None
        self.exp_type = None
        self.exp_pld = None
        tc_list = self.results["testcases"]
        tc_list.append({})
        self.num_tcs += 1
        tc_list[self.num_tcs-1]["tcid"] = self.tc_id
        tc_list[self.num_tcs-1]["payloads"] = []

    def add_payload(self, pld_id, pld_type):
        tc_list = self.results["testcases"]
        pld_list = tc_list[self.num_tcs-1]["payloads"]
        pld_list.append({})
        self.num_plds += 1
        pld_list[self.num_plds-1][pld_id] = {}
        pld_list[self.num_plds-1][pld_id]["type"] = pld_type

    def passed(self, pld_id):
        tc_list = self.results["testcases"]
        pld_list = tc_list[self.num_tcs-1]["payloads"]
        if pld_list[self.num_plds-1][pld_id]["type"] == "NEG":
            pld_list[self.num_plds-1][pld_id]["result"] = "FAILED"
            self.results["num_noks"] += 1
        else:
            pld_list[self.num_plds-1][pld_id]["result"] = "PASSED"
            self.results["num_oks"] += 1

    def failed(self, pld_id):
        tc_list = self.results["testcases"]
        pld_list = tc_list[self.num_tcs-1]["payloads"]
        if pld_list[self.num_plds-1][pld_id]["type"] == "NEG":
            pld_list[self.num_plds-1][pld_id]["result"] = "PASSED"
            self.results["num_oks"] += 1
        else:
            pld_list[self.num_plds-1][pld_id]["result"] = "FAILED"
            self.results["num_noks"] += 1

    def result(self, pld_id):
        tc_list = self.results["testcases"]
        pld_list = tc_list[self.num_tcs-1]["payloads"]
        return pld_list[self.num_plds-1][pld_id]["result"]

    def get_id(self):
        return self.tc_id

    def get_results(self):
        return self.results

    def store_rx_one(self, rx_pld):
        logger = logging.getLogger()

        self.rx_pld = rx_pld

    def set_exp_type(self, exp_type):
        logger = logging.getLogger()

        self.exp_type = exp_type

    def store_exp_one(self, exp_pld):
        logger = logging.getLogger()

        self.exp_pld = exp_pld

    def validate_one(self):
        logger = logging.getLogger()

        if not self.rx_pld:
            raise RuntimeError("No received payload stored!")
        if not self.exp_pld:
            raise RuntimeError("No expected payload stored!")
        if not TestCompare.compare_py_objs(self.rx_pld, self.exp_pld):
            logger.debug("Expected payload:\n{}".format(
                json.dumps(self.exp_pld, indent=2, sort_keys=True)))
            logger.debug("Received payload:\n{}".format(
                json.dumps(self.rx_pld, indent=2, sort_keys=True)))
            return False

        return True

