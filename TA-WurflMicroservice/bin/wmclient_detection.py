import logging
import os
import sys
import re
import json
from splunklib.client import connect
import splunklib.results as results
from wmclient import WmClient, WmClientError

splunk_base_dir = os.environ.get("SPLUNK_HOME")
logfile = splunk_base_dir + '/var/log/splunk/wm_index_migration.log'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
wm_client = None
# change level to error when done
logging.basicConfig(filename=logfile, level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger('wm_client')
try:
    # ------------------------ WM client creation and setup --------------------------------------
    wm_client = WmClient.create("http", "localhost", 8080, "")
    req_caps = ["complete_device_name", "brand_name", "device_os", "device_os_version", "is_mobile",
                "is_tablet", "form_factor"]
    wm_client.set_requested_capabilities(req_caps)

    # ------------------------ Splunk service and inputs retrieval -------------------------------
    # TODO: make this configurable
    service = connect(host='localhost', port=8089, username='admin', password='Crotalo$179')
    # workaround for "Must use user context of 'nobody' when interacting with collection configurations" error message
    service.namespace['owner'] = 'Nobody'
    splunk_indexes = service.indexes
    # TODO: make this configurable
    index_name = "apache_test"
    dst_index = "dst_index"
    src_index = splunk_indexes[index_name]
    if src_index is None:
        logger.error("Source index " + index_name + "does not exist, exiting input script")
        sys.exit(1)
    #  index exist, create new destination index, if it does not exist
    # TODO: make this configurable
    new_index = None
    if dst_index not in splunk_indexes:
        new_index = splunk_indexes.create(dst_index)
        logger.debug("Index " + dst_index + " created")
    else:
        new_index = splunk_indexes[dst_index]
        logger.debug("Index " + dst_index + " retrieved")

    # load items. TODO: handle offset/pagination. It'd be better to load a group of events , copy them to a new index
    #  and keep a checkpoint
    logger.debug("index type: " + str(type(src_index)))
    # index_content = src_index.content
    # logger.debug(str(index_content))

    rr = results.ResultsReader(service.jobs.export("search index="+index_name))
    for result in rr:
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
            logger.debug(user_agent)
            logger.debug("--------------------------------------------")
            device = wm_client.lookup_useragent(user_agent)
            # ------------- Enrich item with WURFL data ----------------------------------
            for rc in req_caps:
                item_dict[rc] = device.capabilities[rc]
            item_dict["wurfl_id"] = device.capabilities["wurfl_id"]
            logger.debug(item_dict)
            # ------------- Create an item to submit to index ----------------------------
            new_index.submit(event=json.dumps(item_dict) , host=item_dict["host"],
                             source="apache_test", sourcetype="wurfl_enriched_access_combined")
            logger.debug("new event submitted")

except WmClientError as e:
    logger.error(e.message)
finally:
    if wm_client is not None:
        wm_client.destroy()
