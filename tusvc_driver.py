# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

import json
import pprint
import logging

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
        self.exp_pld = None
        tc_list = self.results["testcases"]
        tc_list.append({})
        self.num_tcs += 1
        tc_list[self.num_tcs-1]["tcid"] = self.tc_id
        tc_list[self.num_tcs-1]["payloads"] = []

    def passed(self, pld_id):
        tc_list = self.results["testcases"]
        pld_list = tc_list[self.num_tcs-1]["payloads"]
        pld_list.append({})
        self.num_plds += 1
        pld_list[self.num_plds-1][pld_id] = "PASSED"
        self.results["num_oks"] += 1

    def failed(self, pld_id):
        tc_list = self.results["testcases"]
        pld_list = tc_list[self.num_tcs-1]["payloads"]
        pld_list.append({})
        self.num_plds += 1
        pld_list[self.num_plds-1][pld_id] = "FAILED"
        self.results["num_noks"] += 1

    def get_id(self):
        return self.tc_id

    def get_results(self):
        return self.results

    def store_rx_one(self, rx_pld):
        logger = logging.getLogger()

        self.rx_pld = rx_pld

    def store_exp_one(self, exp_pld):
        logger = logging.getLogger()

        self.exp_pld = exp_pld

    def validate_one(self):
        logger = logging.getLogger()

        if not self.rx_pld:
            raise RuntimeError("No received payload stored!")
        if not self.exp_pld:
            raise RuntimeError("No expected payload stored!")
        if self.rx_pld != self.exp_pld:
            logger.debug("Expected payload:\n{}".format(
                pprint.PrettyPrinter().pformat(self.exp_pld)))
            logger.debug("Received payload:\n{}".format(
                pprint.PrettyPrinter().pformat(self.rx_pld)))
            return False

        return True

