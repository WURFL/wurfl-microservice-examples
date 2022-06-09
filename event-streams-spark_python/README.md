# WURFL Microservice pyspark streaming demo app

## Requirements
- Python 3.x
- Pip
- Java 8 or above (for Spark)
- Pyspark 3.1.3 or above (3.0.x version are not suggested due to some known vulerability)
- Pandas 1.1.3 (for csv output creation)
- pycurl (on which WURFL Microservice client API depends)
- pylru
- WURFL Microservice client API 2.1.0 or above

if you don't already have these packages you can install them using pip

```
pip install pyspark
pip install pandas
pip install pycurl
pip install pylru
pip install wmclient
```

## Running the app 

Executing the app requires that you have a wurfl microservice instance up and running 
(be it a Docker image or a VM instance on AWS, Azure o Google Cloud)

**python ./spark_processor --ip <WM server IP> --port <WM server port>**
  
## Sending data to the Spark application
We use netcat to send data via TCP socket to the demo app:

cd into the project root directory and run the following command

**nc -lk 9999 < event_stream_mid_compr.json**

- Note: the file analysis.py contains some data frames for extracting capabilities data to csv files
