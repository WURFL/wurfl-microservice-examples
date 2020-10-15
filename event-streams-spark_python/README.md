# WURFL Microservice pyspark streaming demo app

## Requirements
- Python 3.x
- Java 8 or above (for Spark)
- Pyspark 3.0.0 or above
- WURFL Microservice client API 2.1.0
- Pandas 1.1.3 (for csv output creation)
- pycurl (on which WURFL Microservice client API depends)

## Running app 

python ./spark_processor --ip <WM server IP> --port <WM server port>
  
## Sending data to the Spark application
We use netcat to send data via TCP socket to the demo app:

cd into the project root directory and run the following command

**nc -lk 9999> < vent_stream_mid_compr.json**
