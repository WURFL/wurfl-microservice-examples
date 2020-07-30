package com.scientiamobile.wurflmicroservice.eventprocessor;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.scientiamobile.wurfl.wmclient.Model;
import com.scientiamobile.wurfl.wmclient.WmClient;
import com.scientiamobile.wurfl.wmclient.WmException;
import org.apache.spark.*;
import org.apache.spark.streaming.*;
import org.apache.spark.streaming.api.java.*;

public class SparkProcessor {

    private static final String RECEIVER_HOST = "localhost";
    private static final int RECEIVER_PORT = 9999;


    public static void main(String[] args) throws WmException {

        // Context configuration:
        // - executed locally
        // - uses four working threads
        // - One second time interval at which streaming data will be divided into batches
        SparkConf conf = new SparkConf().setMaster("local[4]").setAppName("WurflDeviceDetection");
        JavaStreamingContext jssc = new JavaStreamingContext(conf, Durations.seconds(1));


        // Let's create an instance of WURFL Microservice client, which we will use for device detection tasks
        WmClient wmClient = WmClient.create("http", "<WM_SERVER_IP_HERE>", "80", "");
        // Set a cache size for WM client (note that size must be bigger in a production environment)
        wmClient.setCacheSize(20000);

        // We'll use a Gson parser to parse events into Java objects
        Gson gson = new GsonBuilder().setPrettyPrinting().create();

        // We create a socket receiver running at localhost:9999 to which events will be streamed
        JavaReceiverInputDStream<String> stream = jssc.socketTextStream(RECEIVER_HOST, RECEIVER_PORT);
        // Maps string events to parsed Java objects
        JavaDStream<EnrichedEventData> events = stream.map(s -> gson.fromJson(s, EnrichedEventData.class));
        // Now enrich the received event object with device detection data
        JavaDStream<EnrichedEventData> enrichedEvents = events.map(ev -> performDeviceDetection(wmClient, ev));


    }

    private static EnrichedEventData performDeviceDetection(WmClient wmClient, EnrichedEventData ev) {

        try {
            HttpServletRequestMock request = new HttpServletRequestMock(ev.getHeaders());
            Model.JSONDeviceData device = wmClient.lookupRequest(request);
            ev.setWurflCompleteName(device.capabilities.get("complete_device_name"));
            ev.setWurflDeviceMake(device.capabilities.get("brand_name"));
            ev.setWurflDeviceModel(device.capabilities.get("model_name"));
            ev.setWurflFormFactor(device.capabilities.get("form_factor"));
            ev.setWurflDeviceOS(device.capabilities.get("device_os") + " " + device.capabilities.get("device_os_version"));

            // TODO: print result, or maybe do some nice aggregation
        } catch (WmException e) {
            // ...handle detection error (most of the times some connection/transfer exception from the WM server)
        }
        return ev;
    }
}
