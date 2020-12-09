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
Install this add-on by simply copying all the whole project directory under `$SPLUNK_HOME/etc/apps`
You'll have to download and add all the dependencies under `$SPLUNK_HOME/etc/apps/TA-WurflMicroservice/bin` 

### Basic script configuration
The file `default/inputs.conf` contains the basic configurations for both `wm_index_migration` and `wm_log_forensic_input`.
It looks like this

```
[script://./bin/wm_index_migration.py]
interval = 300
sourcetype = access_combined
disabled = False
```

The first line declares the relative path of the script to be executed. 
The path is relative to the Splunk app-on installation dir (ie path is resolved to:
 `$SPLUNK_HOME/etc/apps/TA-WurflMicroservice/bin/wm_index_migration.py`)
 Line 2 is the interval in seconds between each script execution. In case you must migrate a massive amount of data,
 you should choose a time span big enough to allow the script to complete before the next execution or, better, 
 configure it to run once and then switch to the periodic execution once the first massive migration has ended.
 Line 3 describes the source type of the original data
 Line 4 is used to enable/disable script execution
  

### Use cases in detail

- Use case 1: **migrate data from a Splunk index that contains data loaded from
 apache `access_combined` log files to a new index that contains the same data enriched with 
 WURFL device detection `capabilities`**
 
 Script `bin/wm_index_migration.py` does the following:
 - defines its own log file and format
 - dynamically loads configuration parser library depending on running Python version
 - loads custom script configuration
 - creates an instance of WURFL Microservice client
 - verifies that source index exist
 - creates the new destination index
 - check that source index has items to import (which happens when import is executed after the first time)
 - fetches data from the source index
 - extracts the user agent from the source data items
 - performs a device detection using `wm_client.lookup_useragent(useragent)`
 - enriches the data items with WURFL capabilities
 - saves the enriched item to the destination index

 The script custom configuration are located int `bin/inputs.conf.spec`. This is a sample configuration
 
```
[wurfl_index_migration]
user = admin
pwd  = Q3JvdGFsbyQxNzk=
host = localhost
port = 8089
src_index = apache_test
dst_index = wurfl_index
wm_host = localhost
wm_port = 8080
wm_cache_size = 200000
capabilities = brand_name,complete_device_name,device_os,device_os_version,form_factor,is_mobile,is_tablet
```

`user` and `password` are the credentials of the internal splunk user. They are needed to access the splunk
services via its REST API. For the sake of this example password is base64 encoded but you can (and should)
replace the code with a more secure encoding of your choice
 `host` and `port` are the ones that expose Splunk REST API endpoints
 `src_index` is the name of the index that contains the data to migrate
 `dst_index` is the name of the destination index where enriched data are copied
 `wm_host` and `wm_port` are the ones exposed by WURFL Microservice server running on
  AWS/Azure/GCP/Docker image.
 `wm_cache_size` is the size of WURFL Microservice client cache
 `caoabilities` is a comma separated list of WURFL capabilities that you want to use to enrich log data
  
  All configuration parameters are mandatory
 
 - Use case 2: **load data from apache `mod_log_forensic` files, enrich them with  WURFL device detection 
 `capabilities` and save them to an index.**
 
 Script `bin/wm_log_forensic_input.py` does the following:
 
 - defines its own log file and format
 - dynamically loads configuration parser library depending on running Python version
 - loads custom script configuration
 - creates an instance of WURFL Microservice client
 - loads or create a checkpoint index (used to resume data load if Splunk is shut down or input files are updated with new data)
 - loads the data source file or directory
 - for each file to read:
    - fetches data from the file
    - extracts the HTTP headers of the original request
    - performs a device detection using `wm_client.lookup_headers(headers)`
    - enriches the data items with WURFL capabilities
    - saves the enriched item to the destination index
 - writes checkpoint data when necessary
 
 The script custom configuration are located int `bin/inputs.conf.spec`. This is a sample configuration
 
```
[wurfl_log_forensic_input]
user = admin
pwd  = Q3JvdGFsbyQxNzk=
host = localhost
port = 8089
src_fs = /home/andrea/splunk_inputs/forensic_1k.log
dst_index = wurfl_forensic
wm_host = localhost
wm_port = 8080
wm_cache_size = 200000
capabilities = brand_name,complete_device_name,device_os,device_os_version,form_factor,is_mobile,is_tablet
checkpoint_row_span = 500
```

Many parameters are the same as the migration script with some exception.
Data source parameter is `src_fs`: it can be the full path of a log forensic file or en entire directory: in that case every file inside the directory
will be loaded into the Splunk index.
`checkpoint_row_span` is the numer of rows that must be read before a write to the checkpoint index is done. 
Checkpoint index is used to keep track of how many rows have been read from each file in case the files have been updated and a new script execution must
read only the newly added lines.

### Script execution

Starting or restarting Splunk with the command `$SPLUNK_HOME/bin/splunk start/restart` causes an immediate execution of the script. From that moment on,
it will be executed according to the `interval` parameter value.
