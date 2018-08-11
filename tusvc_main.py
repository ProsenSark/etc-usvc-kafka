#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# -*- coding: utf-8 -*-

from __future__ import print_function
from tusvc_driver import TestCaseDriver
from tusvc_ms import TestProducer, TestConsumer
from tusvc_serdes import TestSerializer
from tusvc_payload import TestPayload
import sys, os
import getopt
import yaml
import logging

def setup_logging():
    """Setup logging, which is thread-safe &
    is more preferable to debug print"""
    chndl = logging.StreamHandler(sys.stdout)
    chndl.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s " +
                                  "%(module)s - %(funcName)s: %(message)s",
                                  "%Y-%m-%d %H:%M:%S")
    chndl.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #logger.setLevel(logging.DEBUG)
    logger.addHandler(chndl)

def load_yaml(yaml_file):
    """Load YAML file"""
    logger = logging.getLogger()

    logger.debug("Loading YAML file '%s' ..." % yaml_file)

    try:
        with open(yaml_file, 'r') as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as e:
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            logger.error("Not able to load YAML file '%s', error position: (%s:%s)"
                    % (yaml_file, mark.line+1, mark.column+1))
    except:
        logger.error("Not able to load YAML file '%s'" % yaml_file)

    # check there is information in the YAML file
    if not data:
        logger.warning("The YAML file '%s' is empty" % yaml_file)

    return data

def collect_report(tc_drv):
    results = tc_drv.get_results()

    hdr1 = ("+------------------------------------------------------------------------------+\n" +
            "|                             Task Result Details                              |\n" +
            "+------------------------------------------------------------------------------+")
    print("\n" + hdr1)
    for tc in results["testcases"]:
        print(" {} ".format(tc["tcid"]))
        for pld in tc["payloads"]:
            for key, val in pld.items():
                print("     {:<60s}  {:>10s} ".format(key, val["result"]))

    hdr2 = ("+------------------------------------------------------------------------------+\n" +
            "|                             Task Result Summary                              |\n" +
            "+------------------------------------------------------------------------------+")
    print("\n" + hdr2)
    total_str = "TOTAL: {},".format(results["num_oks"] + results["num_noks"])
    passed_str = "PASSED: {},".format(results["num_oks"])
    failed_str = "FAILED: {}".format(results["num_noks"])
    print("     {:>28s} {:s} {:<20s} ".format(total_str, passed_str, failed_str))
    print("")

def run_testcases(config):
    logger = logging.getLogger()

    if not isinstance(config, dict):
        raise TypeError("'config' must be of type 'dict'")
    if "testcases" not in config:
        raise RuntimeError("'testcases' NOT found")
    if not isinstance(config["testcases"], list):
        raise TypeError("'testcases' must be of type 'list'")

    tc_drv = TestCaseDriver()

    tc_num = 0
    for tc in config["testcases"]:
        tc_num += 1
        err_hdr = "TC #{}: ".format(tc_num)

        if not isinstance(tc, dict):
            raise TypeError(err_hdr + "Each testcase must be of type 'dict'")

        if "tcid" not in tc:
            raise RuntimeError(err_hdr + "'tcid' NOT found")
        tc_id = tc["tcid"]
        tc_drv.reinit(tc_id)

        if "source" not in tc:
            raise RuntimeError(err_hdr + "'source' NOT found")
        tc_src_cfg = tc["source"]
        tc_src = TestProducer(tc_drv, tc_src_cfg)

        if "sink" not in tc:
            raise RuntimeError(err_hdr + "'sink' NOT found")
        tc_sink_cfg = tc["sink"]
        tc_sink = TestConsumer(tc_drv, tc_sink_cfg)

        if "serialize" not in tc_src_cfg:
            raise RuntimeError(err_hdr + "'serialize' NOT found in 'source' dict")
        tc_src_serial_cfg = tc_src_cfg["serialize"]
        if "serialize" not in tc_sink_cfg:
            raise RuntimeError(err_hdr + "'serialize' NOT found in 'sink' dict")
        tc_sink_serial_cfg = tc_sink_cfg["serialize"]
        tc_serial = TestSerializer(tc_drv, tc_src_serial_cfg, tc_sink_serial_cfg)

        if "payloads" not in tc:
            raise RuntimeError(err_hdr + "'payloads' NOT found")
        if not isinstance(tc["payloads"], list):
            raise TypeError(err_hdr + "'payloads' must be of type 'list'")

        pld_num = 0
        for pld in tc["payloads"]:
            pld_num += 1
            err2_hdr = err_hdr + "PLD #{}: ".format(pld_num)

            if not isinstance(pld, dict):
                raise TypeError(err2_hdr + "Each payload must be of type 'dict'")

            pld_id = "PLD #{}".format(pld_num)
            log_hdr = "<{}: {}> ".format(tc_id, pld_id)
            try:
                tc_pld = TestPayload(tc_num, tc_id, pld, pld_num)
                pld_id = tc_pld.get_id(tc_src.get_type(), tc_sink.get_type())
                pld_type = tc_pld.get_type()
                tc_drv.add_payload(pld_id, pld_type)
                log_hdr = "<{}: {}> ".format(tc_id, pld_id)

                tx_pld = tc_pld.get_tx_pld(tc_src.get_type())
                exp_pld = tc_pld.get_exp_pld(tc_src.get_type(), tc_sink.get_type())

                tc_sink.flush()

                logger.debug(log_hdr + "Tx 1 msg")
                tc_src.tx_one(tc_serial.serialize(tx_pld))

                logger.debug(log_hdr + "Rx 1 msg")
                tc_serial.deserialize(tc_sink.rx_one(), exp_pld)

                logger.debug(log_hdr + "Validate 1 msg")
                if tc_drv.validate_one():
                    tc_drv.passed(pld_id)
                else:
                    tc_drv.failed(pld_id)
            except Exception as exc:
                logger.error("Oops! {}".format(str(exc)))
                tc_drv.failed(pld_id)
                #raise

            pld_result = tc_drv.result(pld_id)
            if pld_result == "PASSED":
                logger.info("The result of testcase {} is => {}".format(
                    log_hdr, pld_result))
            elif pld_result == "FAILED":
                logger.error("The result of testcase {} is => {}".format(
                    log_hdr, pld_result))

    collect_report(tc_drv)

def print_usage_and_exit(program_name):
    sys.stderr.write("Usage: %s [options...] -f <test-suite yaml file>\n" % (program_name))
    options = ("  Options:\n" +
            "    -v, --verbose      Enable verbose output\n" +
            "    -h, --help         Display this information\n")
    sys.stderr.write(options)
    sys.exit(1)

def main():
    logger = logging.getLogger()

    if len(sys.argv) == 1:
        print_usage_and_exit(sys.argv[0])

    yaml_cfg = None
    try:
        opt_list, argv = getopt.getopt(sys.argv[1:], 'f:vh',
                ['verbose', 'help',])
        if len(argv) != 0:
            print_usage_and_exit(sys.argv[0])

        for opt, arg in opt_list:
            if opt == '-f':
                try:
                    yaml_cfg = str(arg)
                except ValueError:
                    sys.stderr.write("Invalid option value for -f: %s\n" % (arg))
                    sys.exit(1)
            elif opt in ('-v', '--verbose'):
                logger.setLevel(logging.DEBUG)
            elif opt in ('-h', '--help'):
                print_usage_and_exit(sys.argv[0])

        if not yaml_cfg:
            print_usage_and_exit(sys.argv[0])
    except Exception as exc:
        sys.stderr.write("%s\n" % (str(exc)))
        print_usage_and_exit(sys.argv[0])

    config = load_yaml(yaml_cfg)
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(config)
    if not config:
        logger.error("Oops! Empty YAML config '%s'" % (yaml_cfg))
        return

    try:
        run_testcases(config)
    except Exception as exc:
        logger.error("Oops! {}".format(str(exc)))
        #raise

if __name__ == "__main__":
    setup_logging()

    main()

