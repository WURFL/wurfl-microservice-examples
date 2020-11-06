import logging
import os
import sys
from time import sleep

from splunklib.client import connect
from xml.dom import minidom
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
    service = connect(host='localhost', port=8089, username='admin', password='')
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

    search_name = "all_from " + index_name
    saved_search = None
    if search_name not in service.saved_searches:
        query = "index=apache_test"
        saved_search = service.saved_searches.create(search_name, query)
    else:
        saved_search = service.saved_searches[search_name]

    if saved_search is not None:
        job = saved_search.dispatch()

        # Create a small delay to allow time for the update between server and client
        sleep(2)

        # Wait for the job to finish--poll for completion and display stats
        while True:
            job.refresh()
            stats = {"isDone": job["isDone"],
                     "doneProgress": float(job["doneProgress"]) * 100,
                     "scanCount": int(job["scanCount"]),
                     "eventCount": int(job["eventCount"]),
                     "resultCount": int(job["resultCount"])}
            status = ("\r%(doneProgress)03.1f%%   %(scanCount)d scanned   "
                      "%(eventCount)d matched   %(resultCount)d results") % stats

            # logger.debug(status)
            if stats["isDone"] == "1":
                break
            sleep(2)

        # Display the search results now that the job is done
        job_results = job.results()

    content = []
    while True:
        part = job_results.read(1024)
        if len(part) == 0:
            break
        else:
            content.append(part)
    logger.debug("--------------------------------------------I")
    # raw_event = content["raw"]
    logger.debug(content)
    logger.debug(str(type(content)))
    logger.debug("--------------------------------------------E")

    # items = src_index.iter(offset=0, count=None, pagesize=20)
    # items = src_index.list()
    # for item in items:
    #    logger.debug("--------------------------------------------")
    #    logger.debug(item)
    #    logger.debug(item.event)
    #    logger.debug("--------------------------------------------")
    #    user_agent = None
    #    if "user_agent" in item.event:
    #        user_agent = item["user_agent"]
    #    elif "http_user_agent" in item.event:
    #        user_agent = item.event["http_user_agent"]
    #    if user_agent is None or user_agent == '':
    #        logger.debug("item retrieved from index has no user_agent field, skipping")
    #    else:
    #        user_agent = ""
    #         device = wm_client.lookup_useragent(user_agent)
    # ------------- Enrich item with WURFL data ----------------------------------
    # for rc in req_caps:
    #     item.event[rc] = device.capabilities[rc]
    # item.event["wurfl_id"] = device.capabilities["wurfl_id"]
    # logger.debug("enriched item with WURFL capabilities")
    # ------------- Create an item to submit to index ----------------------------
    # new_index.submit(event=item.event, host=item.host, source=item.source, sourcetype=item.sourcetype)
    # logger.debug("new event submitted")

except WmClientError as e:
    logger.error(e.message)
finally:
    if wm_client is not None:
        wm_client.destroy()
