package com.scientiamobile.wurflmicroservice.eventprocessor;

import com.scientiamobile.wurfl.wmclient.WmClient;
import com.scientiamobile.wurfl.wmclient.WmException;

import java.io.Serializable;

public class WmClientProvider implements Serializable {
    private static transient WmClient wmClient = null;

    private WmClientProvider(WmClient client) {
        wmClient = client;
    }

    public static WmClient getOrCreate(String host, String port) throws WmException {
        if(wmClient == null){
            // Let's create an instance of WURFL Microservice client, which we will use for device detection tasks
            wmClient = WmClient.create("http", host, port, "");
            // Set a cache size for WM client (note that size must be bigger in a production environment)
            wmClient.setCacheSize(20000);
        }
        return wmClient;
    }
}
