import base64
from email import utils
import logging
import os
import sys
import re
import json
import time

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
lock_file_path = splunk_base_dir + '/var/log/splunk/wm_index_migration.lock'
logfile = splunk_base_dir + '/var/log/splunk/wm_index_migration.log'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
wm_client = None
# change level to error when done
logging.basicConfig(filename=logfile, level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger('wm_client')
logger.info("Python version: " + py_version)
logger.info("Python legacy version: " + str(legacy_python))


def create_lock_file():
    try:
        f = open(lock_file_path, "w+")
        f.write("This lock file has been created automatically. DO NOT DELETE manually")
        logger.info("lock file created")

    except Exception as e:
        logger.info("Unable to create lock file: %s", e.message)


def delete_lock_file():
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)
        logger.info("wm_index_migration lock file removed")
    else:
        logger.warning("wm_index_migration lock file was not here to delete")


def should_write_checkpoint(chk_point_row_span, l_count):
    logger.debug("Entering should_write_checkout function")
    if chk_point_row_span == 0:
        return True
    if l_count % chk_point_row_span == 0:
        return True
    return False


def write_checkpoints(cp_index, cp_index_name, cp_data, post_del_sleep):
    cp_index.delete()
    logger.info("checkpoint index deleted")
    # we must give a short time to cleanup the index before re-creating it
    sleep_time = float(post_del_sleep)
    time.sleep(sleep_time)
    cp_index = splunk_indexes.create(cp_index_name)
    logger.debug("checkpoint index recreated")
    cp_index.submit(event=json.dumps(cp_data), host="localhost",
                    source="wm_log_forensic_script", sourcetype="scripted_input")
    logger.info("Written checkpoint for checkpoint data %s", cp_data)
    return cp_index


def convert_time_to_timestamp(p_time):
    d = utils.parsedate_tz(p_time)
    return time.mktime(d)


try:
    # ------------------------ Splunk service and index retrieval -------------------------------
    logger.debug("-------------------------------------- STARTING EXECUTION ---------------------------------------")

    # check lock file as first thing, if it exists, script has been called twice
    if os.path.exists("wm_index_migration.lock"):
        logger.warning("wm_index_migration is already running. It can only run one script instance at the time. "
                       "Exiting current script instance")
        exit(1)
    create_lock_file()

    checkpoint_index_name = 'wm_index_migration_checkpoint'
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
        delete_lock_file()
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
        wm_cache_size = config.get("wurfl_index_migration", "wm_cache_size")
        log_arrival_delay = config.get("wurfl_index_migration", "log_arrival_delay")
        checkpoint_row_span = config.get("wurfl_index_migration", "checkpoint_row_span")
        index_post_deletion_sleep = config.get("wurfl_index_migration", "index_post_deletion_sleep")
        logger.debug("--- CONFIGURATION LOADED ----")
    # we must use a broad exception because specialized one is different between Python 2.7 and 3.x
    except Exception as ex:
        logger.error("An error occurred while reading configuration file, likely a wrong or missing key")
        delete_lock_file()
        exit(1)

    # ------------------------ WM client creation and setup --------------------------------------
    wm_client = WmClient.create("http", wm_host, wm_port, "")
    req_caps = concat_cap_list.split(",")
    wm_client.set_requested_capabilities(req_caps)
    wm_client.set_cache_size(int(wm_cache_size))

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

        # Verify if checkpoint index exists. If not, create it
    checkpoint_data = {}
    if checkpoint_index_name not in splunk_indexes:
        checkpoint_index = splunk_indexes.create(checkpoint_index_name)
        checkpoint_index.refresh()
        logger.debug("checkpoint index created")
        checkpoint_data[src_index.name] = 0
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
                item = check_result["_raw"]
                checkpoint_data = json.loads(item)
                logger.info(checkpoint_data)
            else:
                logger.error("No checkpoint item found, exiting")
                exit(1)

    #  now create new destination index, if it does not exist
    new_index = None
    is_first_execution = True
    new_index_evt_count = 0
    if dst_index not in splunk_indexes:
        new_index = splunk_indexes.create(dst_index)
        logger.info("Index " + dst_index + " created")
    else:
        is_first_execution = False
        new_index = splunk_indexes[dst_index]
        new_index_evt_count = new_index["totalEventCount"]
        logger.info(new_index_evt_count)
        if not isinstance(new_index_evt_count, int):
            new_index_evt_count = int(new_index_evt_count)
        logger.info("Index " + dst_index + " retrieved")
        logger.info(new_index_evt_count)
        logger.info(src_index_evt_count)

    # No data have ever been imported, search all
    search_string = "search index=" + index_name + " | reverse"
    if not is_first_execution:
        # set search boundaries
        end_timestamp = time.time() - int(log_arrival_delay)
        str_end_timestamp = str(end_timestamp)
        start_timestamp = checkpoint_data[src_index.name]

        search_string = "search index= {} _indextime>{} _indextime<{} | reverse".format(src_index.name,
                                                                                        start_timestamp,
                                                                                        end_timestamp)

    # before proceeding to enrich src_index events, let's check if there's need to do another search
    logger.info(search_string)
    rr = results.ResultsReader(service.jobs.export(search_string))
    events_migrated = 0
    current_timestamp = 0
    for result in rr:
        # this happens when import into new index has been stopped for some reason (ie: splunk shutdown/restart)
        if isinstance(result, results.Message):
            # Diagnostic messages might be returned in the results
            logger.debug('%s: %s', result.type, result.message)
        elif isinstance(result, dict):
            # Normal events are returned as dicts
            logger.debug("--------------------------------------------")
            item = result["_raw"]
            # current_timestamp = result["_time"]
            current_timestamp = result["_indextime"]
            parts = [
                r'(?P<host>\S+?)',  # host %h
                r'\S+',  # indent %l (unused)
                r'(?P<user>\S+?)',  # user %u
                r'\[(?P<time>.+)\]',  # time %t
                r'"(?P<request>.*?)"',  # request "%r"
                r'(?P<status>[0-9]+?)',  # status %>s
                r'(?P<size>\S+)',  # size %b (careful, can be '-')
                r'"(?P<referrer>.*?)"',  # referrer "%{Referer}i"
                r'"(?P<useragent>.*?)"',  # user agent "%{User-agent}i"
            ]
            try:
                pattern = re.compile(r'\s+'.join(parts) + r'\s*\Z')
                item_dict = pattern.match(item).groupdict()
                user_agent = item_dict["useragent"]
            except Exception:
                logger.error("Unable to parse log line %s, possibly a wrong access_combined format, skipping import", item)
                continue

            device = wm_client.lookup_useragent(user_agent)
            # ------------- Enrich item with WURFL data ----------------------------------
            for rc in req_caps:
                item_dict[rc] = device.capabilities[rc]
            item_dict["wurfl_id"] = device.capabilities["wurfl_id"]
            # logger.debug(item_dict)
            # ------------- Create an item to submit to index ----------------------------
            new_index.submit(event=json.dumps(item_dict), host=item_dict["host"],
                             source="apache_test", sourcetype="wurfl_enriched_access_combined")
            checkpoint_data[src_index.name] = str(current_timestamp)
            events_migrated += 1
            logger.debug("new event submitted")
            if should_write_checkpoint(int(checkpoint_row_span), events_migrated):
                write_checkpoints(checkpoint_index, checkpoint_index_name, checkpoint_data, index_post_deletion_sleep)
            logger.info("Events migrated " + str(events_migrated))
    write_checkpoints(checkpoint_index, checkpoint_index_name, checkpoint_data, index_post_deletion_sleep)
    logger.info("Last checkpoint written: " + str(checkpoint_data[src_index.name]))
    logger.debug("refreshing new index")
    new_index.refresh()
    time.sleep(10)
except WmClientError as e:
    logger.error(e.message)
finally:
    delete_lock_file()
    if wm_client is not None:
        wm_client.destroy()
