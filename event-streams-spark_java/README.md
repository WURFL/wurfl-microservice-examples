# WURFL Microservice Spark Streaming example

This project demonstrates how to use WURFL Microservice client and server to add device detection features to a Spark Streaming Java app.

## Prerequisites

- Spark 2.x and above
- Java 8 and above
- netcat command
- WURFL Microservice server:

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

The compilation output will be a jat file containing the app and all its dependencies

`event-stream-spark-java-demo/<version_number>/event-stream-spark-java-demo-<version_number>-jar-with-dependencies.jar`

## Installing and running the app on Spark

This is the command used to install the app on a standalone Spark installation (for Spark cluster installation please check Sparks documentation)

`<SPARK_HOME>/bin/spark-submit --class com.scientiamobile.wurflmicroservice.eventprocessor.SparkProcessor --master local --deploy-mode client target/event-stream-spark-java-demo-<version>-jar-with-dependencies.jar <WURFL Microservice IP address>`

## Sending data to the Spark app 

Assuming we are on the root directory of the app project we can do 


`nc -lk 9999> < ../event-streams-java/event_streams_min_compr.json`

This will send the content of the json file to the socket listening for data in our application.
Repeat this command two or three times to see the results on the console.

The output will look like this:

!(img/output.png)