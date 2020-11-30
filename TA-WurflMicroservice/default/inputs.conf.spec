[script://./bin/wm_index_migration.py]

[wurfl_index_migration]
user = admin
pwd  = Q3JvdGFsbyQxNzk=
host = localhost
port = 8089
src_index = apache_test
dst_index = wurfl_index
wm_host = localhost
wm_port = 8080
capabilities = brand_name,complete_device_name,device_os,device_os_version,form_factor,is_mobile,is_tablet

[wurfl_log_forensic_input]
user = admin
pwd  = Q3JvdGFsbyQxNzk=
host = localhost
port = 8089
src_fs = /home/andrea/splunk_inputs/forensic_1k.log
dst_index = wurfl_forensic
wm_host = localhost
wm_port = 8080
capabilities = brand_name,complete_device_name,device_os,device_os_version,form_factor,is_mobile,is_tablet
