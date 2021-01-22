# Apache Nifi WURFL device enrich processor
An Apache NiFi processor that enriches a FlowFile attributes with WURFL device data.

### Prerequisites and conditions

- Java 8 or above
- Apache Nifi 12.x
- WURFL Microservice client Java 2.1.2 or above

### Build the Nifi bundle

Apache NiFi component bundles are built into files with **.nar** extension. 
From this project root directory do:

`mvn clean install`

if all tests pass, the archive is created under `$project_root/nifi-wurfl-enrich-processor-nar/target/nifi-wurfl-enrich-processor-nar-1.x.y.nar` 

### Installing .nar file on NiFi

To install the .nar bundle into Apache NiFi drop the file into `$NIFI_HOME/lib`.
Restart NiFi is not needed since it has a .nar autodiscovery and load mechanism
which takes care of making the WURFL Processor discoverable.