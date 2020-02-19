package com.scientiamobile.wurflmicroservice.eventsender;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.FileInputStream;
import java.io.InputStreamReader;

public class Sender {


    public static void main(String args[]) {

        try {
            FileInputStream fis = new FileInputStream("../event_stream.json");
            Gson gson = new GsonBuilder().setPrettyPrinting().create();

            EventData[] data = gson.fromJson(new InputStreamReader(fis), EventData[].class);
            for (EventData event : data){
                event.setTimestamp(System.nanoTime());
                System.out.println(gson.toJson(event));
                Thread.sleep(100);
            }
        } catch (Exception ex) {
            System.out.println("Unable to open json event stream: " + ex.getMessage());
            ex.printStackTrace();
        }

    }

}
