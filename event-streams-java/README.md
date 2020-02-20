# event-streams-demo

Event streams demo for Wurfl Microservice is composed by two small Java applications:

- sender: reads a json file containg some http request data, adds to each request entry a timestamp and sends it to the standard output

- processor: receives the http request json entries on by one from the standard input, uses WURFL microservice client to enrich them with device detection data and sends them to the standard output again.

The applications can work together passing the first one's output to the second one's input via pipe.
### Compiling and launching the demo applications - Java

event-streams demo requires Java 8 or above

Clone this repsitory on your local machine. 
Then:
```sh
cd event-sender
mvn clean package
cd ../event-processor
mvn clean package
java -jar ../event-sender-java/target/event-sender.jar | java -jar target/event-processor.jar --host <wm server IP address>
```

If `host` is not specified, it is assumed to be `localhost`

**Please note that if you run this demo with WURFL Microservice for AWS/Azure you'll need to use a Standard edition or above to have access to all the capabilities used in this demo**
