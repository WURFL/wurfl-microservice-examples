[wurfl_index_migration]
user = admin
pwd  = mybase64encpwd=
host = localhost
port = 8089
src_index = apache_test
dst_index = wurfl_index
wm_host = localhost
wm_port = 8080
wm_cache_size = 200000
capabilities = brand_name,complete_device_name,device_os,device_os_version,form_factor,is_mobile,is_tablet
log_arrival_delay = 300
checkpoint_row_span = 5000
index_post_deletion_sleep=0.9

[wurfl_log_forensic_input]
user = admin
pwd  = mybase64encpwd=
host = localhost
port = 8089
src_fs = /home/andrea/splunk_inputs/forensic_1k.log
dst_index = wurfl_forensic
wm_host = localhost
wm_port = 8080
wm_cache_size = 200000
capabilities = brand_name,complete_device_name,device_os,device_os_version,form_factor,is_mobile,is_tablet
checkpoint_row_span = 500
