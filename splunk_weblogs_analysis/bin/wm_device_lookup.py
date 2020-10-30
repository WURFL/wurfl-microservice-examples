#!/usr/bin/env python

import csv
import logging
import os
import sys
import urllib

from wmclient import WmClient

splunk_base_dir = os.environ.get("SPLUNK_HOME")
logfile = splunk_base_dir + '/var/log/splunk/wm_client.log'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
# change level to error when done
logging.basicConfig(filename=logfile, level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger('wm_client')


def get_or_create_wm_client():
    """Gets or Creates a WM client
          """
    if "WMClient" not in globals():
        globals()["wm_client"] = WmClient.create("http", "localhost", 8080, "")
        logger.debug("WURFL Microservice client created")

    return globals()["wm_client"]


# Main function: entry point for Splunk apps
if __name__ == '__main__':

    wm_client = get_or_create_wm_client()
    info = wm_client.get_info()
    all_caps = info.static_capabilities
    for cap in info.virtual_capabilities:
        all_caps.append(cap)

    r = csv.reader(sys.stdin)
    w = csv.writer(sys.stdout)

    have_header = False
    header = []
    idx = -1
    for row in r:
        if not have_header:
            header = row
            logger.debug('fields found: %s' % header)
            have_header = True
            logger.debug(header)
            z = 0
            for h in row:
                if h == "user_agent":
                    idx = z
                z += 1
            w.writerow(row)
            continue

        # TODO: use all headers to perform a detection
        user_agent = row[idx]
        logger.debug('found user-agent %s' % user_agent)

        logger.debug('executing lookup by user_agent')
        results = []
        try:
            device = wm_client.lookup_useragent(user_agent)
        except Exception as e:
            logger.error(e)
            continue

        # event if data are returned we can get some error
        if device.error is not None and device.error != "":
            logger.error(device.error)
            continue

        logger.debug('Sending out capability values')
        output_row = []
        c = 0
        for header_name in header:
            c += 1
            # logger.debug(str(c) + "-" + header_name)
            if header_name == "user_agent":
                output_row.append(user_agent)
            else:
                if header_name != "OUTPUT":
                    output_row.append(device.capabilities[header_name])

        logger.debug(output_row)
        w.writerow("outrow: " + str(output_row))
        logger.debug('------------- output written -------------')
