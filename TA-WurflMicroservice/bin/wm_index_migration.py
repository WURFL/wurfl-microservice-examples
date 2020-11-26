import base64
import logging
import os
import sys
import re
import json
from time import sleep

from splunklib.client import connect
import splunklib.results as results
from wmclient import WmClient, WmClientError

py_version = sys.version
legacy_python = py_version.startswith('2')
if legacy_python:
    import ConfigParser  # 2.7
else:
    import configparser  # 3.x

splunk_base_dir = os.environ.get("SPLUNK_HOME")
logfile = splunk_base_dir + '/var/log/splunk/wm_index_migration.log'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
wm_client = None
# change level to error when done
logging.basicConfig(filename=logfile, level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger('wm_client')
logger.info("Python version: " + py_version)
logger.info("Python legacy version: " + str(legacy_python))

try:
    # ------------------------ Splunk service and index retrieval -------------------------------
    logger.debug("-------------------------------------- STARTING EXECUTION ---------------------------------------")
    # Load configuration
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
    LOCAL_DIR = os.path.abspath(os.path.join(ROOT_DIR, '..', 'local'))
    DEFAULT_DIR = os.path.abspath(os.path.join(ROOT_DIR, '..', 'default'))
    local_inputs_file = os.path.join(LOCAL_DIR, 'inputs.conf.spec')
    default_inputs_file = os.path.join(DEFAULT_DIR, 'inputs.conf.spec')
    config = configparser.ConfigParser()
    try:
        config.read(open(local_inputs_file))
    except IOError:
        logger.warning("No config file found in local directory: " + LOCAL_DIR)

    try:
        logger.info(default_inputs_file)
        config = configparser.RawConfigParser()
        logger.info("File read: " + str(config.read_file(open(default_inputs_file))))
    except IOError:
        logger.error("No config file found in default directory: " + DEFAULT_DIR +
                     ", exiting WURFL Microservice index enrichment script")
        logger.error("Offending path: " + default_inputs_file)
        sys.exit(1)
    try:
        logger.info("Sections: " + str(config.sections()))
        user = config.get("wurfl_index_migration", "user")
        enc_pwd = config.get("wurfl_index_migration", "pwd")
        pwd_bytes = base64.b64decode(enc_pwd)
        pwd = pwd_bytes.decode('ascii')
        splunk_host = config.get("wurfl_index_migration", "host")
        splunk_port = config.get("wurfl_index_migration", "port")
        wm_host = config.get("wurfl_index_migration", "wm_host")
        wm_port = config.getint("wurfl_index_migration", "wm_port")
        index_name = config.get("wurfl_index_migration", "src_index")
        dst_index = config.get("wurfl_index_migration", "dst_index")
        concat_cap_list = config.get("wurfl_index_migration", "capabilities")
        logger.debug("--- CONFIGURATION LOADED ----")
    # we must use a broad exception because specialized one is different between Python 2.7 and 3.x
    except Exception as ex:
        logger.error("An error occurred while reading configuration file, likely a wrong or missing key")

    # ------------------------ WM client creation and setup --------------------------------------
    wm_client = WmClient.create("http", wm_host, wm_port, "")
    req_caps = concat_cap_list.split(",")
    wm_client.set_requested_capabilities(req_caps)

    # ------------------------ Splunk service and index retrieval -------------------------------
    service = connect(host=splunk_host, port=splunk_port, username=user, password=pwd)
    # workaround for "Must use user context of 'nobody' when interacting with collection configurations" error message
    service.namespace['owner'] = 'Nobody'
    splunk_indexes = service.indexes
    src_index = splunk_indexes[index_name]
    if src_index is None:
        logger.error("Source index " + index_name +
                     "does not exist, exiting WURFL Microservice index enrichment script")
        sys.exit(1)
    src_index_evt_count = src_index["totalEventCount"]
    if not isinstance(src_index_evt_count, int):
        src_index_evt_count = int(src_index_evt_count)
    # logger.debug("------ SRC INDEX TOTAL EVENTS")
    # logger.debug(src_index_evt_count)
    # logger.debug("------ SRC INDEX TOTAL EVENTS")

    #  index exist, create new destination index, if it does not exist
    new_index = None
    new_index_evt_count = 0
    if dst_index not in splunk_indexes:
        new_index = splunk_indexes.create(dst_index)
        logger.info("Index " + dst_index + " created")
    else:
        new_index = splunk_indexes[dst_index]
        new_index_evt_count = new_index["totalEventCount"]
        logger.info(new_index_evt_count)
        if not isinstance(new_index_evt_count, int):
            new_index_evt_count = int(new_index_evt_count)
        logger.info("Index " + dst_index + " retrieved")
        logger.info(new_index_evt_count)
        logger.info(src_index_evt_count)

    # before proceeding to enrich src_index events, let's check if there's need to do another search
    results_count = 0
    if new_index_evt_count >= src_index_evt_count:
        logger.info("Index " + dst_index + " is already up to date with source index " + index_name +
                    " Exiting WURFL Microservice index enrichment script")
        sys.exit(0)

    rr = results.ResultsReader(service.jobs.export("search index=" + index_name))
    for result in rr:
        # this happens when import into new index has been stopped for some reason (ie: splunk shutdown/restart)
        if new_index_evt_count > results_count:
            results_count += 1
            logger.info("result " + str(results_count) + " has already been imported: skipping")
            continue

        results_count += 1
        if isinstance(result, results.Message):
            # Diagnostic messages might be returned in the results
            logger.debug('%s: %s', result.type, result.message)
        elif isinstance(result, dict):
            # Normal events are returned as dicts
            logger.debug("--------------------------------------------")
            item = result["_raw"]
            parts = [
                r'(?P<host>\S+)',  # host %h
                r'\S+',  # indent %l (unused)
                r'(?P<user>\S+)',  # user %u
                r'\[(?P<time>.+)\]',  # time %t
                r'"(?P<request>.*)"',  # request "%r"
                r'(?P<status>[0-9]+)',  # status %>s
                r'(?P<size>\S+)',  # size %b (careful, can be '-')
                r'"(?P<referrer>.*)"',  # referrer "%{Referer}i"
                r'"(?P<useragent>.*)"',  # user agent "%{User-agent}i"
            ]
            pattern = re.compile(r'\s+'.join(parts) + r'\s*\Z')
            item_dict = pattern.match(item).groupdict()
            user_agent = item_dict["useragent"]
            # logger.debug(user_agent)
            # logger.debug("--------------------------------------------")
            device = wm_client.lookup_useragent(user_agent)
            # ------------- Enrich item with WURFL data ----------------------------------
            for rc in req_caps:
                item_dict[rc] = device.capabilities[rc]
            item_dict["wurfl_id"] = device.capabilities["wurfl_id"]
            # logger.debug(item_dict)
            # ------------- Create an item to submit to index ----------------------------
            new_index.submit(event=json.dumps(item_dict), host=item_dict["host"],
                             source="apache_test", sourcetype="wurfl_enriched_access_combined")
            logger.debug("new event submitted")
            logger.info("Results count " + str(results_count))
    logger.info("Results count at scripts end: " + str(results_count))
    logger.info("refreshing new index")
    new_index.refresh()
    sleep(10)
except WmClientError as e:
    logger.error(e.message)
finally:
    if wm_client is not None:
        wm_client.destroy()
