# WURFL Microservice Spark Streaming example

This project demonstrates how to use WURFL Microservice client and server to add device detection features to a Spark Streaming Java app.
We will use `netcat` command to send http request headers data in JSON format to our app via a socket bound on port `9999`

An example of the JSON input is:

```
[{
   "Save-Data":"on",
   "Accept-Language":"en",
   "Accept-Encoding":"gzip, deflate",
   "X-Operamini-Features":"advanced, camera, download, file_system, folding, httpping, pingback, routing, touch, viewport",
   "X-Forwarded-For":"103.38.89.102, 141.0.8.173",
   "Accept":"text/html, application/xml;q=0.9, application/xhtml+xml, image/png, image/webp, image/jpeg, image/gif, image/x-xbitmap, */*;q=0.1",
   "User-Agent":"Opera/9.80 (Android; Opera Mini/39.1.2254/163.76; U; en) Presto/2.12.423 Version/12.16",
   "X-Operamini-Phone-Ua":"Mozilla/5.0 (Linux; Android 9; moto g(6) plus Build/PPWS29.116-16-15; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/73.0.3683.90 Mobile Safari/537.36",
   "Device-Stock-Ua":"Mozilla/5.0 (Linux; Android 9; moto g(6) plus Build/PPWS29.116-16-15; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/73.0.3683.90 Mobile Safari/537.36",
   "Event":"VIDEO_OK",
   "Video-id":"TPhZnruRPsM",
   "Forwarded":"for=\"103.38.89.102:49931\""
}]
```

The app uses the headers data to perform a device detection and enrich the JSON with data such as device brand, model and OS. 
It also does some data aggregation to count how many devices have been detected for each brand.

Application output will look like this:

![](https://github.com/WURFL/wurfl-microservice-examples/blob/1.0.0/event-streams-spark_java/img/output.png)

## Prerequisites

- Spark 2.x and above
- Java 8 and above
- netcat command
- A WURFL Microservice server:

    using WURFL Microservice for Docker/AWS/Azure will allow you to run your own WURFL-based device detection service in your hosting infrastructure by deploying familiar Docker images, AWS ec2 instances or Azure VMs.
    Getting started with WURFL Microservice https://docs.scientiamobile.com/documentation/wurfl-microservice/aws-getting-started
    
    AWS AMIs :
    https://aws.amazon.com/marketplace/pp/B076MB5TRD
    
    Azure VMs :
    https://azuremarketplace.microsoft.com/en-us/marketplace/apps/scientiamobile.wurfl_microservice_2_0_basic
    
    GCP VMs: https://console.cloud.google.com/marketplace/browse?q=WURFL

### Compile the app
From the example app root, do:

`mvn clean install`

The compilation output will be a jar file containing the app and all its dependencies

`event-stream-spark-java-demo/<version_number>/event-stream-spark-java-demo-<version_number>-jar-with-dependencies.jar`

## Installing and running the app on Spark

This is the command used to install and run the app on a standalone Spark installation (for Spark cluster installation please check Spark documentation)

`<SPARK_HOME>/bin/spark-submit --class com.scientiamobile.wurflmicroservice.eventprocessor.SparkProcessor --master local --deploy-mode client <path_to>/event-stream-spark-java-demo-<version>-jar-with-dependencies.jar <WURFL Microservice IP address>`

## Sending data to the Spark app 

Assuming we are on the root directory of the app project we can do 


`nc -lk 9999> < ../event-streams-java/event_streams_min_compr.json`

This will send the content of the json file to the socket listening for data in our application.
Repeat this command two or three times to see the results on the console.

Please note the the app processes the sent data every 30 seconds, so it is possible that you'll have to wait some time to see the results diplayed on console.
