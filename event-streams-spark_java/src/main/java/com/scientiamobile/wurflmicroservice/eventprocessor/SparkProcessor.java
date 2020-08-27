package com.scientiamobile.wurflmicroservice.eventprocessor;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.scientiamobile.wurfl.wmclient.Model;
import com.scientiamobile.wurfl.wmclient.WmClient;
import com.scientiamobile.wurfl.wmclient.WmException;
import org.apache.spark.*;
import org.apache.spark.streaming.*;
import org.apache.spark.streaming.api.java.*;

import java.io.StringReader;
import java.util.HashMap;
import java.util.Map;

public class SparkProcessor {

    private static final String RECEIVER_HOST = "localhost";
    private static final int RECEIVER_PORT = 9999;

    public static void main(String[] args) throws Exception {
        String wmServerHost;
        if (args.length > 0) {
            wmServerHost = args[0];
        } else {
            return;
        }

        final Map<String, Integer> brandCount = new HashMap<>();

        // Context configuration:
        // - executed locally
        // - uses four working threads
        // - One second time interval at which streaming data will be divided into batches
        SparkConf conf = new SparkConf().setMaster("local[4]").setAppName("WurflDeviceDetection");
        JavaStreamingContext jssc = new JavaStreamingContext(conf, Durations.seconds(30));

        // We create a socket receiver running at localhost:9999 to which events will be streamed
        JavaReceiverInputDStream<String> stream = jssc.socketTextStream(RECEIVER_HOST, RECEIVER_PORT);
        // Maps string events to parsed Java objects
        JavaDStream<EnrichedEventData[]> events = stream.map(s -> {
            // We'll use a Gson parser to parse events into Java objects
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            return gson.fromJson(new StringReader(s), EnrichedEventData[].class);
        });
        // Now enrich the received event object with device detection data
        JavaDStream<EnrichedEventData[]> enrichedEvents = events.map(evs -> {
            WmClient wmClient = WmClientProvider.getOrCreate(wmServerHost, "80");
            for (EnrichedEventData evItem : evs) {
                try {
                    HttpServletRequestMock request = new HttpServletRequestMock(evItem.getHeaders());
                    Model.JSONDeviceData device = wmClient.lookupRequest(request);
                    evItem.setWurflCompleteName(device.capabilities.get("complete_device_name"));
                    evItem.setWurflDeviceMake(device.capabilities.get("brand_name"));
                    evItem.setWurflDeviceModel(device.capabilities.get("model_name"));
                    evItem.setWurflFormFactor(device.capabilities.get("form_factor"));
                    evItem.setWurflDeviceOS(device.capabilities.get("device_os") + " " + device.capabilities.get("device_os_version"));
                } catch (WmException e) {
                    // ...handle detection error (most of the times some connection/transfer exception from the WM server)
                }
            }
            return evs;
        });

        enrichedEvents.foreachRDD(evList -> {
            Map<String, Integer> bcount = new HashMap<>();
            evList.foreach(eev -> {
                for (EnrichedEventData e : eev) {
                    System.out.println("---------------------------------------------------------------------------");
                    System.out.println("Complete device name: " + e.getWurflCompleteName());
                    System.out.println("Device OS & version:  " + e.getWurflDeviceOS());
                    System.out.println("Device form factor:    " + e.getWurflFormFactor());
                    System.out.println("---------------------------------------------------------------------------");

                    if (!bcount.containsKey(e.getWurflDeviceMake())) {
                        bcount.put(e.getWurflDeviceMake(), 0);
                    }
                    bcount.put(e.getWurflDeviceMake(), bcount.get(e.getWurflDeviceMake()) + 1);
                }
                System.out.println("--------------------------------------BRAND COUNT -------------------------");
                bcount.forEach((k, v) -> {
                    System.out.println(k + ": " + v);
                });
                System.out.println("---------------------------------------------------------------------------");
            });
        });

        // Let's start the streaming activity and wait for it to end
        jssc.start();
        jssc.awaitTermination();
    }
}