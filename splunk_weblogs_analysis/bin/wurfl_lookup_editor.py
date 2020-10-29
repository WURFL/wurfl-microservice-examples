import logging
import os
import sys
import json
import cherrypy
import io
import configparser  # read transforms.conf
import platform

import splunk.appserver.mrsparkle.controllers as controllers
import splunk.appserver.mrsparkle.lib.util as util
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
from splunk.appserver.mrsparkle.lib.decorators import expose_page

bin_dir = os.path.join(util.get_apps_dir(), __file__.split('.')[-2], 'bin')

if not bin_dir in sys.path:
    sys.path.append(dir)


def setup_logger(level):
    """
    Setup a logger for the REST handler.
    """

    logger = logging.getLogger('splunk.appserver.WurflDetectionForSplunk.controllers.wurfl_lookup_editor')
    logger.propagate = False  # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(
        make_splunkhome_path(['var', 'log', 'splunk', 'wurfl_lookup_editor_controller.log']), maxBytes=25000000,
        backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = setup_logger(logging.INFO)
"""
Represents an exception when the lookup supporting fields not found.
"""


class SupportingFieldsNotFoundException(Exception):
    pass


"""
Represents an exception when the lookup is not updated.
"""


class LookupUpdationFailedException(Exception):
    pass


class LookupDisplay:

    # Class for sending response in object format
    # Constructor for LookupDisplay class to intialize fields
    def __init__(self, fieldsList, commonCapabilities, unCommonCapabilities):
        self.fieldsList = fieldsList
        self.commonCapabilities = commonCapabilities
        self.unCommonCapabilities = unCommonCapabilities


class LookupEditor(controllers.BaseController):
    @expose_page(must_login=True, methods=['POST'])
    def save(self, namespace, existingCapabilities, selectedCapabilities):
        """
        Save the lookupFields to transforms file
        """
        logger.info("Saving lookup with new lookupFields...")
        # getting the present app namespace
        logger.info("namespace: %s \n selectedCapabilities: %s", namespace, selectedCapabilities)
        # converting unicode to str format and adding user_agent field
        selectedCapabilities_string = "user_agent," + str(selectedCapabilities)
        existingCapabilities_string = str(existingCapabilities)
        logger.info("selectedCapabilities_string: %s \n type", selectedCapabilities_string,
                    type(selectedCapabilities_string))
        user = cherrypy.session['user']['name']
        logger.info("user name... %s", user)
        logger.info("start interacting with edit method")
        existingCapabilities_string = "user_agent," + existingCapabilities_string
        lookupFields = ""
        config = None
        destination_full_path = None
        try:
            # accessing lookup from local/transforms.conf
            destination_full_path_local = make_splunkhome_path(['etc', 'apps', namespace, 'local', 'transforms.conf'])
            logger.info("path for transforms file from local:\t %s", destination_full_path_local)
            destination_full_path_default = make_splunkhome_path(
                ['etc', 'apps', namespace, 'default', 'transforms.conf'])
            logger.info("path for transforms file from default :\t %s", destination_full_path_default)
            # checking whether local/transforms.conf file is existing or not
            if os.path.exists(destination_full_path_local):
                # Parsing the transforms configuration file 
                config = configparser.ConfigParser()
                config.readfp(io.open(destination_full_path_local, 'r', encoding='utf_8_sig'))
                # checking whether option and section are existing or not:
                if config.has_option("wurfl_lookup", "fields_list") and config.has_option("wurfl_lookup",
                                                                                          "external_cmd"):
                    # retrieving value of fields_list option under wurfl_lookup section
                    lookupFields = config.get("wurfl_lookup", "fields_list")
                    if existingCapabilities_string == lookupFields:
                        destination_full_path = destination_full_path_local
                        fieldsFound = True
                    else:
                        fieldsFound = False
                else:
                    fieldsFound = False
            else:
                fieldsFound = False
            if not fieldsFound:
                # local/transforms is not found or found but option is not available in the section so accessing from
                # default folder Parsing the transforms configuration file
                config = configparser.ConfigParser()
                config.read_file(open(destination_full_path_default))
                # checking whether option and section are existing or not:
                if config.has_option("wurfl_lookup", "fields_list"):
                    # retrieving value of fields_list option under wurfl_lookup section
                    lookupFields = config.get("wurfl_lookup", "fields_list")
                    if existingCapabilities_string == lookupFields:
                        destination_full_path = destination_full_path_default
                        fieldsFound = True
                    else:
                        fieldsFound = False
                else:
                    fieldsFound = False
            logger.info("lookupFields : %s \n", lookupFields)
            logger.info("Done interacting with transforms path\n")
            if fieldsFound is None or fieldsFound is False:
                raise SupportingFieldsNotFoundException("Error in accessing the fields_list from transforms.conf")
            if fieldsFound is True and not (config is None) and not (destination_full_path is None):
                # retrieving value of external_cmd option under wurfl_lookup section			
                externalCommand = config.get("wurfl_lookup", "external_cmd")
                # retrieving value of fields_list option under wurfl_lookup section
                fields_list = config.get("wurfl_lookup", "fields_list")
                logger.info("Before editing: \n Command: %s \n FieldsList :%s", externalCommand, fields_list)
                # getting the py file name dynamically
                pyFileName = externalCommand.split(" ")[0]
                # Updating new capabilities to the externalCommand 
                externalCommand = pyFileName + " " + selectedCapabilities_string.replace(",", " ")
                # Updating new capabilities to the fields_list 
                fields_list = selectedCapabilities_string.replace(",", ", ")
                logger.info("After editing: \n Command: %s \n FieldsList :%s", externalCommand, fields_list)
                # setting value to fields_list option under wurfl_lookup section
                config.set("wurfl_lookup", "fields_list", fields_list)
                # setting value to external_cmd option under wurfl_lookup section	
                config.set("wurfl_lookup", "external_cmd", externalCommand)
                # saving the updated values to transforms configuration file
                with open(destination_full_path, 'wb') as configfile:
                    config.write(configfile)
                logger.info("Done interacting with edit method\n")
                return "Lookup Capabilities are in Sync with Selected Licensed Capabilities"
            else:
                raise LookupUpdationFailedException("Error in updating the lookup file")
        except IOError:
            cherrypy.response.status = 404
            logger.error("Lookup File not found")
            return ""
        except SupportingFieldsNotFoundException:
            cherrypy.response.status = 405
            logger.error("SupportingFieldsNotFoundException")
            return ""
        except LookupUpdationFailedException:
            cherrypy.response.status = 406
            logger.error("LookupUpdationFailedException")
            return ""
        except Exception as ae:
            logger.error("Error :: " + ae)
            cherrypy.response.status = 500
            return "Lookup Configuration is not updated. Please Try Later"

        # return self.render_json(message, set_mime='application/json')

    def getLookup(self, namespace):
        """
        Get the contents of a lookup file
        """

        logger.info("Getting lookup contents...")
        # getting the present app namespace
        logger.info("namespace: %s", namespace)
        lookupFields = ""
        fieldsFound = None
        try:
            # accessing lookup from local/transforms.conf
            destination_full_path_local = make_splunkhome_path(['etc', 'apps', namespace, 'local', 'transforms.conf'])
            logger.info("path for transforms file from local:\t %s", destination_full_path_local)
            destination_full_path_default = make_splunkhome_path(
                ['etc', 'apps', namespace, 'default', 'transforms.conf'])
            logger.info("path for transforms file from default :\t %s", destination_full_path_default)
            # checking whether local/transforms.conf file is existing or not
            if os.path.exists(destination_full_path_local):
                logger.info(" File is existing at local folder ")
                # Parsing the transforms configuration file 
                config = configparser.ConfigParser()
                config.readfp(io.open(destination_full_path_local, 'r', encoding='utf_8_sig'))
                logger.info(" connected to config and read ")
                # checking whether option and section are existing or not:
                if config.has_option("wurfl_lookup", "fields_list") and config.has_option("wurfl_lookup",
                                                                                          "external_cmd"):
                    logger.info(" config has option ")
                    # retrieving value of fields_list option under wurfl_lookup section
                    lookupFields = config.get("wurfl_lookup", "fields_list")
                    fieldsFound = True
                else:
                    fieldsFound = False
                    logger.info(" config has no option ")
            else:
                fieldsFound = False
            logger.info(" fieldsFound %s ", fieldsFound)
            if fieldsFound is False:
                # local/transforms is not found or found but option is not available in the section so accessing from
                # default folder Parsing the transforms configuration file
                config = configparser.ConfigParser()
                config.readfp(open(destination_full_path_default))
                # checking whether option and section are existing or not:
                if config.has_option("wurfl_lookup", "fields_list") and config.has_option("wurfl_lookup",
                                                                                          "external_cmd"):
                    # retrieving value of fields_list option under wurfl_lookup section
                    lookupFields = config.get("wurfl_lookup", "fields_list")
                    fieldsFound = True
                else:
                    fieldsFound = False
            logger.info("lookupFields : %s \n", lookupFields)
            logger.info("Done interacting with getLookup method\n")
            if fieldsFound is None or fieldsFound == False:
                raise SupportingFieldsNotFoundException("Error in accessing the fields_list from transforms.conf")
        except IOError:
            cherrypy.response.status = 404
            logger.error("Lookup File not found")
            pass
        except SupportingFieldsNotFoundException:
            cherrypy.response.status = 405
            logger.error("SupportingFieldsNotFoundException")
            pass
        except Exception as ae:
            cherrypy.response.status = 500
            logger.error("Error when attempting to make a backup; the backup will not be made" + ae)
            pass
        return lookupFields

    def getAllWURFLCapabilities(self, namespace):
        """
        Get the capabilities of a wurfl file
        """

        logger.info("Getting wurfl capabilities ...")
        logger.info("start")
        wurfl_capabilities = ""
        try:
            destination_full_path = make_splunkhome_path(['etc', 'apps', namespace, 'bin', 'config.properties'])
            logger.info("path for config.properties :\t" + destination_full_path)
            # Identifying the os of the system
            os_section = ""
            WurfldconfigFilePath = ""
            osname = platform.system()
            if "Windows" == osname:
                os_section = "windows"
            elif "Linux" == osname:
                os_section = "linux"
            elif "Darwin" == osname:
                os_section = "mac"
            # Reading config.properties present in app's bin folder with configparser
            config = configparser.ConfigParser()
            config.readfp(open(destination_full_path))
            # Reading the WurfldconfigFilePath value
            if config.has_option(os_section, "WurfldconfigFilePath"):
                WurfldconfigFilePath = config.get(os_section, "WurfldconfigFilePath")
            logger.info("path for wurfld config file :\t" + WurfldconfigFilePath)
            # Removing double quotes from path
            configfile = WurfldconfigFilePath.replace("\"", "")
            # Parsing wurfld config file located at the path retrieved
            wurfldconfig = configparser.ConfigParser()
            wurfldconfig.readfp(open(configfile))
            # value of license_path option under wurfld section
            license_path = wurfldconfig.get("wurfld", "license_path")
            logger.info("path for license file :\t %s", license_path)
            # Reading license file located at the path retrieved
            licenseconfig = open(license_path)
            separator = ":"
            keys1 = {}
            # reading each property as a line and spliting with separator as : and storing to dict
            for line in licenseconfig:
                if separator in line:
                    name, value = line.split(separator, 1)
                    keys1[name.strip()] = value.strip()
            # Closing the file object connected to license file
            licenseconfig.close()
            # Retrieving the list of licensed capabilities
            wurfl_capabilities = keys1["wurfl_capabilities"]
            logger.info("wurfl capabilities :\t" + wurfl_capabilities)
            logger.info("Done")
        except IOError:
            cherrypy.response.status = 404
            logger.error("File not found at wurflCapabilities")
            pass
        except Exception as ae:
            cherrypy.response.status = 500
            logger.error("Error when attempting to make a backup; the backup will not be made" + ae)
            pass
        return wurfl_capabilities

    @expose_page(must_login=True, methods=['POST'])
    def getLookupDisplay(self, namespace):
        """
        Get the contents from lookup contents,wurfl_capabilities and display  
        """
        lookupDisplay_json = ""
        try:
            # get lookup supporting fields list
            lookupFields = self.getLookup(namespace)
            # get licensed wurfl capabilities
            allWurflCapabilities = self.getAllWURFLCapabilities(namespace)
            allWurflCapabilitiesList = allWurflCapabilities.split(",")  # converting str to list while spliting with ","
            lookupFieldsList = lookupFields.split(",")  # converting str to list while spliting with ","
            lookupFieldsList.remove("user_agent")
            unCommonList = []
            commonList = []
            # Seperating the capabilities which are not supported and supported till now by lookup and storing to the unCommonList list and the commonList list successfully
            for cap in allWurflCapabilitiesList:
                if lookupFields.find(cap) == -1:
                    unCommonList.append(cap)
                else:
                    commonList.append(cap)  # get common capabilities from lookup fields and wurflCapabilities
            unCommonListCapabilities = ",".join(unCommonList)  # converting list to comma seperated str
            commonListCapabilities = ",".join(commonList)  # converting list to comma seperated str
            finalLookupCapabilities = ",".join(lookupFieldsList)
            # create object to the LookupDisplay Class
            lookupDisplay = LookupDisplay(finalLookupCapabilities, commonListCapabilities, unCommonListCapabilities)
            # Serialize obj to a JSON formatted str
            lookupDisplay_json = json.dumps(lookupDisplay.__dict__)
            logger.info("json : %s \n data type: %s", lookupDisplay_json, type(lookupDisplay_json))
        except IOError:
            cherrypy.response.status = 404
            return ""
        except Exception as ae:
            cherrypy.response.status = 500
            logger.exception("Error when attempting to get the existing lookup fields \n" + ae)
            return ""
        return self.render_json(lookupDisplay_json, set_mime='application/json')
