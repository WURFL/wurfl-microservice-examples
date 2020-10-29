import json
import threading
import pylru

import logging
import urllib3

__version__ = "2.2.0"
__client_version__ = "wurfl-microservice-python_%s" % __version__
__default_http_timeout__ = 10
config_path = ""

logger = logging.getLogger("wurfl-microservice")


class JsonDeviceOsVersion:

    def __init__(self, info_dict):
        self.device_os = info_dict["device_os"]
        self.device_os_version = info_dict["device_os_version"]


class JSONModelMktName:

    def __init__(self, info_dict):
        self.brand_name = info_dict["brand_name"]
        self.model_name = info_dict["model_name"]


def to_lower_keys_dict(headers):
    lc_dict = dict()
    for key in headers:
        lc_dict[key.lower()] = headers[key]
    return lc_dict


class WmClient:

    def __init__(self):
        self.staticCaps = []
        self.virtualCaps = []
        self.ltime = None
        self.scheme = "http"
        self.host = ""
        self.port = 80
        self.base_uri = ""
        self.device_makes = []
        self.requested_static_caps = []
        self.requested_virtual_caps = []
        self.important_headers = []
        self.device_os_lock = threading.Lock()
        self.device_makes_lock = threading.Lock()
        self.device_OSes = []
        self.head_cache_lock = threading.Lock()
        self.dev_cache_lock = threading.Lock()
        self.make_models = []
        self.device_makes = []
        self.device_os_versions_dict = dict()
        self.internal_client = urllib3.PoolManager(num_pools=200, maxsize=200, timeout=__default_http_timeout__)

        # caches: by default client has none. Yet it is strongly recommended to set them up.
        self.dev_id_cache = None
        self.head_cache = None

    @staticmethod
    def create(scheme, host, port, baseURI):
        """Creates a new WURFL Microservice client. The client has a default timeout of 10 seconds (set as 10000
        milliseconds). If not scheme is give, client assumes a 'http' value."""
        client = WmClient()
        if len(scheme) > 0:
            client.scheme = scheme
        client.host = host
        client.port = port
        client.base_uri = baseURI

        info = client.get_info()
        client.important_headers = info.important_headers
        client.staticCaps = sorted(info.static_capabilities)
        client.virtualCaps = sorted(info.virtual_capabilities)
        client.ltime = info.ltime

        return client

    def set_http_timeout(self, timeout):
        """Sets HTTP connection timeout in seconds"""
        if timeout is None or timeout <= 0:
            self.internal_client = urllib3.PoolManager(num_pools=200, maxsize=200, timeout=timeout)

    def destroy(self):
        """Closes and deallocates all resources used to connect to server.
        Function calls made after this one will cause error"""
        self.clear_caches()
        self.internal_client = None

    def get_info(self):
        """Returns info about WURFL microservice server.
        It raises a WmClientError in case of connection errors/timeouts"""

        msg = "Client creation failed. Unable to connect to WURFL microservice server - "

        try:
            # performs a GET and get status again
            res = self.internal_client.request("GET", self.__create_URL("/v2/getinfo/json"))
            res_code = res.status

            if 200 <= res_code < 400:
                info = json.loads(res.data.decode('utf-8'))
                res.release_conn()
                self.clear_cache_if_needed(info["ltime"])
                return JsonInfoData(info)
            else:
                msg = "get_info - Unable to get WURFL microservice server info - response code: " + str(res_code)
                logging.error(msg)
                raise WmClientError(msg)

        except Exception as e:
            err_msg_tpl = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = err_msg_tpl.format(type(e).__name__, e.args)
            raise WmClientError(message)

    def __create_URL(self, path):
        url = self.scheme + "://" + self.host
        if self.port > 0:
            url += ":" + str(self.port)
        if len(self.base_uri) > 0:
            return url + "/" + self.base_uri + path
        else:
            return url + path

    def has_static_capability(self, capName):
        """returns True if the given static capability is handled by this client, False otherwise"""
        return capName in self.staticCaps

    def has_virtual_capability(self, capName):
        """returns True if the given virtual capability is handled by this client, False otherwise"""
        return capName in self.virtualCaps

    def set_requested_static_capabilities(self, capsList):
        """sets the list of static capabilities handled by this client"""
        if capsList is None:
            self.requested_static_caps = None
            self.clear_caches()
            return

        stCaps = []
        for name in capsList:
            if self.has_static_capability(name):
                stCaps.append(name)

        self.requested_static_caps = stCaps
        self.clear_caches()

    def set_requested_virtual_capabilities(self, capsList):
        """sets the list of virtual capabilities handled by this client"""
        if capsList is None:
            self.requested_virtual_caps = None
            self.clear_caches()
            return

        vCaps = []
        for name in capsList:
            if self.has_virtual_capability(name):
                vCaps.append(name)

        self.requested_virtual_caps = vCaps
        self.clear_caches()

    def set_requested_capabilities(self, capsList):
        """sets the list of virtual and static capabilities handled by this client"""
        if capsList is None:
            self.requested_static_caps = None
            self.requested_virtual_caps = None
            self.clear_caches()
            return

        capNames = []
        vcapNames = []

        for name in capsList:
            if self.has_static_capability(name):
                capNames.append(name)
            else:
                if self.has_virtual_capability(name):
                    vcapNames.append(name)

        if len(capNames) > 0:
            self.requested_static_caps = capNames

        if len(vcapNames) > 0:
            self.requested_virtual_caps = vcapNames
        self.clear_caches()

    def set_cache_size(self, size):
        """
        Creates a new LRU cache with the given size or, if cache has already been created, increases the size to
        given value.
        :param size: new size of the cache
        """
        if self.dev_id_cache is None:
            self.dev_id_cache = pylru.lrucache(10000)

        if self.head_cache is None:
            self.head_cache = pylru.lrucache(size)
        else:
            self.head_cache.size(size)

    def clear_caches(self):
        if self.head_cache is not None:
            with self.head_cache_lock:
                self.head_cache.clear()

        if self.dev_id_cache is not None:
            with self.dev_cache_lock:
                self.dev_id_cache.clear()

        self.make_models = []
        self.device_makes = []

        with self.device_os_lock:
            self.device_OSes = []
            self.device_os_versions_dict = dict()

    def clear_cache_if_needed(self, ltime):
        if ltime is not None and not (ltime == self.ltime):
            self.ltime = ltime
            self.clear_caches()

    def get_actual_cache_size(self):

        csize = [0] * 2

        with self.dev_cache_lock:
            if self.dev_id_cache is not None:
                csize[0] = len(self.dev_id_cache)

        with self.head_cache_lock:
            if self.head_cache is not None:
                csize[1] = len(self.head_cache)

        return csize

    def safe_put_device(self, cache_type, key, device):
        """
        Puts the device in the cache corresponding to the key value if it has been initialized
        :param cache_type: the type of cache to which save the element
        :param key: the cache type
        :param device: the device to store in cache
        """

        if cache_type == HEADERS_CACHE_TYPE:
            if self.head_cache is not None:
                with self.head_cache_lock:
                    self.head_cache[key] = device

        elif cache_type == DEVICE_ID_CACHE_TYPE:
            if self.dev_id_cache is not None:
                with self.dev_cache_lock:
                    self.dev_id_cache[key] = device

    def __internal_request(self, path, req):

        if req is None:
            raise WmClientError("Request object cannot be None")

        cache_key = None
        device = None
        if DEVICE_ID_CACHE_TYPE == req.cache_type:
            cache_key = req.wurfl_id
        elif HEADERS_CACHE_TYPE == req.cache_type:
            cache_key = req.get_headers_cache_key()

        # First, do a cache lookup
        if req.cache_type is not None and len(req.cache_type) > 0 and cache_key is not None and len(cache_key) > 0:
            if req.cache_type == DEVICE_ID_CACHE_TYPE and self.dev_id_cache is not None:
                with self.dev_cache_lock:
                    device = self.dev_id_cache.get(req.wurfl_id)
                if device is not None:
                    return device
            elif req.cache_type == HEADERS_CACHE_TYPE and self.head_cache is not None:
                with self.head_cache_lock:
                    device = self.head_cache.get(cache_key)

        if device is not None:
            return device

        # No device found in cache, do a server lookup

        try:
            # prepares request payload
            payload = json.dumps(req.__dict__).encode('utf-8')

            res = self.internal_client.request(
                'POST',
                self.__create_URL(path),
                body=payload,
                headers={'Content-Type': 'application/json'})

            res_code = res.status

            if 200 <= res_code < 400:
                json_response = json.loads(res.data.decode(encoding='UTF-8'))
                device = JsonDeviceData(json_response)
                res.release_conn()

                if device.error != "":
                    raise WmClientError("Unable to complete request to WM server: " + device.error)

                # check if cache must be cleared
                self.clear_cache_if_needed(device.ltime)
                # add device to cache
                if device is not None and len(cache_key) > 0:
                    self.safe_put_device(req.cache_type, cache_key, device)

        except Exception as e:
            if isinstance(e, WmClientError):
                raise e
            else:
                msg = self.__format_except_message__(e, "Unable to complete request to WM server: ")
                logging.error(msg)
                raise WmClientError(msg)

        return device

    def lookup_useragent(self, useragent):
        """performs a device detection from the given User-Agent. If the User-Agent is None or empty a generic device
        is returned """
        headers = {"User-Agent": useragent}
        request = Request(lookup_headers=headers, requestedCaps=self.requested_static_caps,
                          requestedVcaps=self.requested_virtual_caps, wurflId=None, cache_type=HEADERS_CACHE_TYPE,
                          important_headers=self.important_headers)
        return self.__internal_request("/v2/lookupuseragent/json", request)

    def lookup_request(self, req):

        """performs a device detection from the headers carried by the given HTTP request.
        The request object is assumed to be the one used in requests python framework.
        If the User-Agent header is None or empty a generic device
                is returned """
        if req is None:
            raise WmClientError("requests.Request cannot be None")

        reqHeaders = dict()
        for hname in self.important_headers:
            if hname in req.headers:
                hval = req.headers[hname]
                if len(hval) > 0:
                    reqHeaders[hname] = hval

        request = Request(lookup_headers=reqHeaders, requestedCaps=self.requested_static_caps,
                          requestedVcaps=self.requested_virtual_caps, wurflId=None,
                          important_headers=self.important_headers, cache_type=HEADERS_CACHE_TYPE)
        return self.__internal_request("/v2/lookuprequest/json", request)

    def lookup_headers(self, headers):

        """performs a device detection from the given headers map.
        The request object is assumed to be the one used in requests python framework.
        If the User-Agent header is None or empty a generic device
                is returned """
        if headers is None:
            raise WmClientError("headers dictionary cannot be None")

        lowerCaseHeaders = to_lower_keys_dict(headers)

        reqHeaders = dict()
        for hname in self.important_headers:
            lower_name = hname.lower()
            if lower_name in lowerCaseHeaders:
                hval = lowerCaseHeaders[lower_name]
                if len(hval) > 0:
                    reqHeaders[hname] = hval

        request = Request(lookup_headers=reqHeaders, requestedCaps=self.requested_static_caps,
                          requestedVcaps=self.requested_virtual_caps, wurflId=None,
                          important_headers=self.important_headers, cache_type=HEADERS_CACHE_TYPE)
        return self.__internal_request("/v2/lookuprequest/json", request)

    def lookup_device_id(self, wurflId):
        """Retrieves a device with the given WURFL ID. If the WURFL ID is None, empty or wring a WMClientError is
        raised """

        request = Request(lookup_headers=None, requestedCaps=self.requested_static_caps,
                          requestedVcaps=self.requested_virtual_caps, wurflId=wurflId,
                          important_headers=self.important_headers, cache_type=DEVICE_ID_CACHE_TYPE)
        return self.__internal_request("/v2/lookupdeviceid/json", request)

    def get_all_OSes(self):
        """:return a list of all device OS"""
        self.__load_device_OSes_data()
        return self.device_OSes

    def __load_device_OSes_data(self):
        self.device_os_lock.acquire()
        devOsNotEmpty = (self.device_OSes is not None) & (len(self.device_OSes) > 0)
        if devOsNotEmpty:
            if self.device_os_lock.locked():
                self.device_os_lock.release()
            return

        try:
            url = self.__create_URL("/v2/alldeviceosversions/json")
            res = self.internal_client.request("GET", url)
            res_code = res.status
            if not (200 <= res_code < 400):
                raise WmClientError("Unable to get device OSes data - response code: " + str(res_code))
            else:
                strOSes = json.loads(res.data.decode(encoding='UTF-8'))
                res.release_conn()
            devOses = []
            ddict = dict()
            for osVer in strOSes:

                devOsVer = JsonDeviceOsVersion(osVer)
                if devOsVer.device_os not in devOses:
                    devOses.append(devOsVer.device_os)

                if devOsVer.device_os not in ddict:
                    ddict[devOsVer.device_os] = []
                ddict[devOsVer.device_os].append(devOsVer.device_os_version)

            if not self.device_os_lock.locked():
                self.device_os_lock.acquire()
            self.device_OSes = devOses
            self.device_os_versions_dict = ddict
            self.device_os_lock.release()
        except Exception as e:
            msg = self.__format_except_message__(e, "An error occurred getting device os name and version data - {}"
                                                 .format(str(e)))
            logging.error(msg)
            raise WmClientError(msg)
        finally:
            if self.device_os_lock.locked():
                self.device_os_lock.release()

    def get_all_versions_for_OS(self, osName):
        """:return a list of all the known versions for the given device OS"""
        self.__load_device_OSes_data()
        if osName in self.device_os_versions_dict:
            osVers = self.device_os_versions_dict[osName]
            for ver in osVers:
                if "" == ver:
                    osVers.remove(ver)
            return osVers
        else:
            msg = "Error getting data from WM server: {} does not exist".format(osName)
            raise WmClientError(msg)

    def __load_device_makes_data(self):
        try:
            # If deviceMakes cache has values everything has already been loaded, thus we exit
            self.device_makes_lock.acquire()
            if len(self.device_makes) > 0:
                return
        finally:
            self.device_makes_lock.release()

            # No values already loaded, let's do it.
        try:
            url = self.__create_URL("/v2/alldevices/json")
            res = self.internal_client.request("GET", url)
            res_code = res.status
            if not (200 <= res_code < 400):
                raise WmClientError("Unable to get device makers data - response code: " + str(res_code))
            else:
                localMakeModels = json.loads(res.data.decode(encoding='UTF-8'))
                res.release_conn()

                dmMap = dict()
                devMakes = []
                for jmkModel in localMakeModels:
                    mkModel = JSONModelMktName(jmkModel)
                    if mkModel.brand_name not in dmMap:
                        devMakes.append(mkModel.brand_name)

                    mdMkNames = dmMap.get(mkModel.brand_name)
                    if mdMkNames is None:
                        mdMkNames = []
                    dmMap[mkModel.brand_name] = mdMkNames

                    mdMkNames.append(mkModel)
                    self.deviceMakesMap = dmMap
                    self.device_makes = devMakes
        except Exception as e:
            msg = self.__format_except_message__(e, "An error occurred getting makes and model data ")
            logging.error(msg)
            raise WmClientError(msg)

    def get_all_device_makes(self):
        """:return a list of all device makers"""
        self.__load_device_makes_data()
        return self.device_makes

    def get_all_devices_for_make(self, make):
        """:return a list of all device models for the given maker"""
        self.__load_device_makes_data()

        if make in self.deviceMakesMap:
            mdMks = self.deviceMakesMap[make]
            return mdMks
        else:
            msg = "Error getting data from WM server: {} does not exist".format(make)
            raise WmClientError(msg)

    def cache_info(self):
        """
        This method is deprecated since version 2.2.0 and will always return None. Use get_actual_cache_size instead
        :return the current state of WMClient internal cache (hits, misses, max size)"""
        return None

    def get_api_version(self):
        """:return the version of this WM Client"""
        return __client_version__

    def __format_except_message__(self, e, msg):
        if hasattr(e, 'message'):
            fmsg = msg + e.message
            return fmsg
        else:
            return msg


class WmClientError(Exception):
    def __init__(self, message):
        self.message = message


HEADERS_CACHE_TYPE = "head-cache"
DEVICE_ID_CACHE_TYPE = "dId-cache"


class JsonInfoData:

    def __init__(self, info_dict):
        self.wurfl_api_version = info_dict["wurfl_api_version"]
        self.wurfl_info = info_dict["wurfl_info"]
        self.wm_version = info_dict["wm_version"]
        self.important_headers = info_dict["important_headers"]
        self.static_capabilities = info_dict["static_caps"]
        self.virtual_capabilities = info_dict["virtual_caps"]
        self.ltime = info_dict["ltime"]


class JsonDeviceData:

    def __init__(self, info_dict):
        self.error = info_dict["error"]
        self.api_version = info_dict["apiVersion"]
        self.capabilities = info_dict["capabilities"]
        self.mtime = int(info_dict["mtime"])
        self.ltime = info_dict["ltime"]


class Request:
    def __init__(self, lookup_headers, requestedCaps, requestedVcaps, wurflId, cache_type, important_headers):
        self.lookup_headers = lookup_headers
        self.requested_caps = requestedCaps
        self.requested_vcaps = requestedVcaps
        self.wurfl_id = wurflId
        self.cache_type = cache_type
        self.important_headers = important_headers
        self.key = None

    def get_headers_cache_key(self):

        if self.key is not None:
            return self.key

        key = ""
        if (self.lookup_headers is None or len(self.lookup_headers) == 0) \
                & (HEADERS_CACHE_TYPE == self.cache_type):
            self.key = ""
            return key

        # if cache type is device id we use wurfl_id as cache key
        if DEVICE_ID_CACHE_TYPE == self.cache_type:
            self.key = self.wurfl_id
            return self.key

        # Using important headers array preserves header name order
        for h in self.important_headers:
            if h in self.lookup_headers:
                hval = self.lookup_headers[h]
                if hval is not None:
                    key += hval
        self.key = key
        return self.key
