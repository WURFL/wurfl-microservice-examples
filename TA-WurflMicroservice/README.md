# Splunk addon for WURFL Microservice integration

This project contains scripts and default configurations 
to use WURFL Microservice client to enrich input data that are saved into a Splunk index or
or have to be loaded into Splunk from a log file.

 ### Prerequisites and dependencies
 
 - Python version 2.7 and 3.x.
 - Splunk 8.0.x
 
 
 They depend on the following libraries:
    
    - pylru (1.2.0-py2.7)
    - urllib3
    - wmclient 2.2.0 or above (https://pypi.org/project/wmclient/)
    - splunklib
    
   This project assumes that you have a basic knowledge of Splunk and [scripted inputs](https://docs.splunk.com/Documentation/SplunkCloud/latest/AdvancedDev/ScriptSetup)

### Use cases

The scripts are configured as *scripted input* on Splunk and cover two specific use cases, 
but everyone can easily write their own code to cover their preferred use cases
using this code as reference for WURFL Microservice integration on Splunk.

### Add-on installation
TODO

- Use case 1: **migrate data from a Splunk index that contains data loaded from
 apache `access_combined` log files to a new index that contains the same data enriched with 
 WURFL device detection `capabilities`**
 
 
 - Use case 2: **load data from apache `mod_log_forensic` files, enrich them with  WURFL device detection 
 `capabilities` and save them to an index.**
 
  