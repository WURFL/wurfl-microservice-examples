import logging
import os
import sys
import json
import cherrypy
import configparser  # read transforms.conf

import splunk.appserver.mrsparkle.controllers as controllers
import splunk.appserver.mrsparkle.lib.util as util
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
from splunk.appserver.mrsparkle.lib.decorators import expose_page

WM_SERVER_SECTION = "wm_server"

bin_dir = os.path.join(util.get_apps_dir(), __file__.split('.')[-2], 'bin')

if bin_dir not in sys.path:
    sys.path.append(dir)


def setup_logger(level):
    """
    Setup a logger for the REST handler.
    """

    logger = logging.getLogger('splunk.appserver.WurflDetectionForSplunk.controllers.wurfl_config_editor')
    logger.propagate = False  # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(
        make_splunkhome_path(['var', 'log', 'splunk', 'wurfl_config_editor_controller.log']), maxBytes=25000000,
        backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = setup_logger(logging.INFO)
"""
Represents an exception when the properties not found in the config.properties.
"""


class SupportingFieldsNotFoundException(Exception):
    pass


"""
Represents an exception when the config.properties is not updated.
"""


class ConfigUpdationFailedException(Exception):
    pass


class ConfigDisplay:

    # Class for sending response in object format
    # Constructor for ConfigDisplay class to initialize fields
    def __init__(self, server_ip, server_port):

        self.wm_server_ip = server_ip
        self.wm_server_port = server_port


class ConfigEditor(controllers.BaseController):
    @expose_page(must_login=True, methods=['POST'])
    def save(self, namespace, wm_server_ip, wm_server_port):
        """
        Saves the configurations to the config.properies file 
        """
        logger.info("Saving config.properies with new Configurations...")
        # displaying the parameters received to logger
        logger.info("namespace: %s \n serverip: %s \n serverport: %s", namespace, wm_server_ip, wm_server_port)

        user = cherrypy.session['user']['name']
        logger.info("user name... %s", user)
        config = None

        try:
            # Enclosing the spaced words in paths with double quotes
            config_full_path = make_splunkhome_path(['etc', 'apps', namespace, 'bin', 'config.properties'])
            logger.info("path for config file:\t %s", config_full_path)
            # checking whether bin/config.properties file is existing or not
            if os.path.exists(config_full_path):
                # Parsing the configuration file 
                config = configparser.ConfigParser()
                config.read_file(open(config_full_path))
                logger.info("config file is read ")
                # checking whether option and section are existing or not if exists then proceeding to read the
                # configurations
                if config.has_option(WM_SERVER_SECTION, "ip") and config.has_option(WM_SERVER_SECTION, "port"):
                    logger.info(" config has WM client mandatory creation options")
                    # retrieving options under os_section and server section
                    wmClientIp = config.get(WM_SERVER_SECTION, "ip")
                    wmClientPort = config.get(WM_SERVER_SECTION, "port")
                    # saving back the updated values to configuration file
                    with open(config_full_path, 'wb') as configfile:
                        config.write(configfile)
                        logger.info("Done writing to file\n")
                    return "Configurations are modified successfully"
            else:
                raise ConfigUpdationFailedException("Error in updating the config.properties file")
        except IOError:
            cherrypy.response.status = 404
            logger.error("Config.properties File not found")
            return "config.properties file is not Found"
        except SupportingFieldsNotFoundException:
            cherrypy.response.status = 405
            logger.error("SupportingFieldsNotFoundException")
            return ""
        except ConfigUpdationFailedException as cufe:
            cherrypy.response.status = 406
            logger.error("ConfigUpdationFailedException")
            return cufe.message
        except Exception as ae:
            logger.error("Error :: " + ae.message)
            cherrypy.response.status = 500
            return "Config.properties is not updated. Please Try Later"

        # return self.render_json(message, set_mime='application/json')

    def get_config(self, namespace):
        """
        Get the contents of a Config.properties file
        """

        logger.info("Getting Config contents...")
        # Logging the present app namespace
        logger.info("namespace: %s", namespace)

        wm_server_ip = ""
        wm_server_port = ""
        fieldsFound = None
        try:
            # accessing configurations from bin/config.properties
            config_full_path = make_splunkhome_path(['etc', 'apps', namespace, 'bin', 'config.properties'])
            logger.info("path for Config.properties file from bin:\t %s", config_full_path)
            # checking whether bin/config.properties file is existing or not
            if os.path.exists(config_full_path):
                logger.info(" File is existing at bin folder ")
                # Parsing the configuration file 
                config = configparser.ConfigParser()
                config.read_file(open(config_full_path))
                logger.info(" connected to config and read ")
                # checking whether options and sections are existing or not:
                if config.has_option(WM_SERVER_SECTION, "ip") and config.has_option(WM_SERVER_SECTION, "port"):
                    logger.info("GET config - config has all options ")
                    # retrieving values of wmClient file paths under os_section and replacing the double quotes of
                    # spaced words with empty value
                    wm_server_ip = config.get(WM_SERVER_SECTION, "ip")
                    wm_server_port = config.get(WM_SERVER_SECTION, "port")
                    fieldsFound = True
                else:
                    fieldsFound = False
                    logger.info(" config has no option ")
            else:
                fieldsFound = False
            logger.info(" fieldsFound %s ", fieldsFound)
            logger.info("WM server ip : %s \n", wm_server_ip)
            logger.info("WM server port : %s \n", wm_server_port)
            logger.info("Done interacting with getConfig method\n")
            if fieldsFound is None or fieldsFound is False:
                raise SupportingFieldsNotFoundException("Error in accessing the configurations from config.properies")
            else:
                configDisplay = ConfigDisplay(wm_server_ip, wm_server_port)
        except IOError:
            cherrypy.response.status = 404
            logger.error("config.properties not found")
            pass
        except SupportingFieldsNotFoundException:
            cherrypy.response.status = 405
            logger.error("SupportingFieldsNotFoundException")
            pass
        except Exception:
            cherrypy.response.status = 500
            logger.error("Error when attempting to retrieve fields from config.properies")
            pass
        return configDisplay

    @expose_page(must_login=True, methods=['POST'])
    def getConfigDisplay(self, namespace):
        """
        Get the contents from lookup contents,wurfl_capabilities and display  
        """
        configDisplay_json = ""
        try:
            # get configurations from config.properties
            configDisplay = self.get_config(namespace)
            # Serialize obj to a JSON formatted str
            configDisplay_json = json.dumps(configDisplay.__dict__)
            logger.info("json : %s \n data type: %s", configDisplay_json, type(configDisplay_json))
        except IOError:
            cherrypy.response.status = 404
            return ""
        except Exception as ae:
            cherrypy.response.status = 500
            logger.exception("Error when attempting to get the existing config fields \n" + ae)
            return ""
        return self.render_json(configDisplay_json, set_mime='application/json')

    @expose_page(must_login=True, methods=['POST'])
    def restoreToDefaultPaths(self, namespace):
        """
        Get the contents from lookup contents,wurfl_capabilities and display  
        """

        try:
            # default
            wm_server_ip = "127.0.0.1"
            wm_server_port = "8080"

            # Object creation for configDisplay
            configDisplay = ConfigDisplay(wm_server_ip, wm_server_port)
            # Serialize obj to a JSON formatted str
            configDisplay_json = json.dumps(configDisplay.__dict__)
            logger.info("json : %s \n data type: %s", configDisplay_json, type(configDisplay_json))
        except IOError:
            cherrypy.response.status = 404
            return ""
        except Exception as ae:
            cherrypy.response.status = 500
            logger.exception("Error when attempting to get the existing config fields \n" + ae)
            return ""
        return self.render_json(configDisplay_json, set_mime='application/json')