package com.scientiamobile.wurflmicroservice.eventprocessor;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import com.scientiamobile.wurfl.wmclient.Model;
import com.scientiamobile.wurfl.wmclient.WmClient;
import com.scientiamobile.wurfl.wmclient.WmException;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Processor class receives JSON events one by one from the standard input, uses the WURFL Microservice client
 * to enrich them with device detection data and prints them back to the standard output.
 */
public class Processor {

    public static void main(String[] args) throws IOException {

        List<String> errors = new ArrayList<>();

        String host = "localhost";
        switch (args.length) {
            case 0:
                // keeps default host
                break;
            case 2:
                host = args[1];
                break;
            default:
                System.out.print("Usage: event-processor-demo [--host <WURFL microservice serve IP>]");
                System.exit(1);
        }

        WmClient wmClient = null;
        try {
            wmClient = WmClient.create("http", host, "80", "");
            wmClient.setCacheSize(20000);
        } catch (WmException e) {
            System.out.println("Unable to connect to host: " + host);
            System.out.println(e.getMessage());
            System.exit(1);
        }
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        JsonReader reader = new JsonReader(new InputStreamReader(System.in));
        reader.setLenient(true);
        JsonToken token = reader.peek();
        while (token!= JsonToken.END_DOCUMENT && reader.hasNext()) {
            EnrichedEventData eventData = gson.fromJson(reader, EnrichedEventData.class);
            try {
                Model.JSONDeviceData device = wmClient.lookupUseragent(eventData.getUserAgent());
                eventData.setWurflCompleteName(device.capabilities.get("complete_device_name"));
                eventData.setWurflDeviceMake(device.capabilities.get("brand_name"));
                eventData.setWurflDeviceModel(device.capabilities.get("model_name"));
                eventData.setWurflFormFactor(device.capabilities.get("form_factor"));
                eventData.setWurflDeviceOS(device.capabilities.get("device_os") + " " + device.capabilities.get("device_os_version"));

                System.out.println(gson.toJson(eventData));
                token = reader.peek();

            } catch (WmException e) {
                errors.add("Cannot get device information for user-agent: " + eventData.getUserAgent());
            } catch (Exception e) {
                errors.add("Error: " + e.getMessage());
            }
            if (errors.size() > 0) {
                createErrorReport(errors);
            }
        }
        reader.close();
    }

    private static void createErrorReport(List<String> errors) {
        File reportFile = new File("error_reports.txt");
        if (!reportFile.exists()) {
            try {
                reportFile.createNewFile();
                OutputStream fw = new FileOutputStream(reportFile);
                BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(fw, StandardCharsets.UTF_8));

                for (String s : errors) {
                    bw.write(s);
                    bw.newLine();
                }

                bw.flush();
                bw.close();

            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
