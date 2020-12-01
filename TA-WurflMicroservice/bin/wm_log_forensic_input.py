import base64
import logging
import os
import sys
import json
import time

from splunklib.client import connect
import splunklib.results as results
from wmclient import WmClient, WmClientError

py_version = sys.version
legacy_python = py_version.startswith('2')
if legacy_python:
    import ConfigParser
else:
    import configparser

splunk_base_dir = os.environ.get("SPLUNK_HOME")
logfile = splunk_base_dir + '/var/log/splunk/wm_log_forensic_input.log'
checkpoint_index_name = 'wm_forensic_checkpoint'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
wm_client = None
# change level to error when done
logging.basicConfig(filename=logfile, level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger('wm_client')

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

    logger.info("Sections: " + str(config.sections()))
    user = config.get("wurfl_log_forensic_input", "user")
    enc_pwd = config.get("wurfl_log_forensic_input", "pwd")
    pwd_bytes = base64.b64decode(enc_pwd)
    pwd = pwd_bytes.decode('ascii')
    splunk_host = config.get("wurfl_log_forensic_input", "host")
    splunk_port = config.get("wurfl_log_forensic_input", "port")
    wm_host = config.get("wurfl_log_forensic_input", "wm_host")
    wm_port = config.getint("wurfl_log_forensic_input", "wm_port")
    src_file_system = config.get("wurfl_log_forensic_input", "src_fs")
    dst_index = config.get("wurfl_log_forensic_input", "dst_index")
    concat_cap_list = config.get("wurfl_log_forensic_input", "capabilities")
    logger.debug("--- LOG FORENSIC: CONFIGURATION LOADED ----")
    file_list = []
    # check if file system element exists and, if its a directory, get all file list
    is_dir_source = os.path.isdir(src_file_system)
    if is_dir_source:
        file_list = os.listdir(src_file_system)
    else:
        file_list.append(src_file_system)
    logger.info(file_list)

    # ------------------------ WM client creation and setup --------------------------------------
    wm_client = WmClient.create("http", wm_host, wm_port, "")
    req_caps = concat_cap_list.split(",")
    wm_client.set_requested_capabilities(req_caps)

    # ------------------------ Splunk service and index retrieval -------------------------------
    service = connect(host=splunk_host, port=splunk_port, username=user, password=pwd)
    # workaround for "Must use user context of 'nobody' when interacting with collection configurations" error message
    service.namespace['owner'] = 'Nobody'
    splunk_indexes = service.indexes
    # Verify if checkpoint index exists. If not, create it
    checkpoint_data = {}
    if checkpoint_index_name not in splunk_indexes:
        checkpoint_index = splunk_indexes.create(checkpoint_index_name)
        checkpoint_index.refresh()
        logger.info("checkpoint index created")
        for f_name in file_list:
            checkpoint_data[f_name] = 0
        checkpoint_index.submit(event=json.dumps(checkpoint_data), host="localhost",
                                source="wm_log_forensic_script", sourcetype="scripted_input")
    else:
        checkpoint_index = splunk_indexes[checkpoint_index_name]
        # read checkpoint values if any
        check_rr = results.ResultsReader(service.jobs.export("search index=" + checkpoint_index_name))
        for check_result in check_rr:
            if isinstance(check_result, results.Message):
                # Diagnostic messages might be returned in the results
                logger.debug('%s: %s', check_result.type, check_result.message)
            elif isinstance(check_result, dict):
                # Normal events are returned as dicts
                logger.info("--------------------------------------------1")
                item = check_result["_raw"]
                checkpoint_data = json.loads(item)
                logger.info(checkpoint_data)
            else:
                logger.error("No checkpoint item found, exiting")
                exit(1)

    # Verify if destination index exists. If not, create it
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

    # For each configured file, get checkpoint and start reading data from that point on
    for filename in file_list:
        checkpoint = checkpoint_data[filename]
        logger.info("checkpoint value: " + str(checkpoint))
        f = open(filename)
        line_count = 0
        line = f.readline()
        logger.info(line)
        while len(line) > 0:
            if line.startswith('-'):
                logger.info("line starts with -")
                line_count += 1
                logger.info("count line " + str(line_count))
                line = f.readline()
                continue
            elif line_count > checkpoint:
                logger.info("line starts with +")
                logger.info("Performing detection on line " + str(line_count))
                tokens = line.split('|')
                host = "-"
                headers = dict()
                headers["forensic_id"] = tokens[0]
                headers["request"] = tokens[1]
                headers["_raw"] = line
                for tok in tokens:
                    if ':' in tok:
                        header = tok.split(':')
                        if header[0] == "Host":
                            host = header[1]
                        headers[header[0]] = header[1]
                device = wm_client.lookup_headers(headers)
                if device is not None:
                    selected_caps = dict()
                    for rc in req_caps:
                        selected_caps[rc] = device.capabilities[rc]
                    selected_caps["wurfl_id"] = device.capabilities["wurfl_id"]
                    new_index.submit(event=json.dumps(selected_caps), host=host,
                                     source=filename, sourcetype="wurfl_enriched_log_forensic")
                    logger.info("new event submitted")
                    new_index.refresh()
                    line_count += 1
                    line = f.readline()
                checkpoint_data[filename] = line_count
                # Delete, recreate and write new checkpoint index
                checkpoint_index.delete()
                logger.info("checkpoint index deleted")
                time.sleep(1)
                checkpoint_index = splunk_indexes.create(checkpoint_index_name)
                logger.info("checkpoint index recreated")
                checkpoint_index.submit(event=json.dumps(checkpoint_data), host="localhost",
                                    source="wm_log_forensic_script", sourcetype="scripted_input")


except WmClientError as e:
    logger.error(e.message)
finally:
    if wm_client is not None:
        wm_client.destroy()