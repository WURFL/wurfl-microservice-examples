package com.scientiamobile.wurflmicroservice.eventsender;

import com.google.gson.annotations.SerializedName;

/**
 * Event data class is the model for the data arriving from the JSON event stream. The only data which is added
 * during this phase if the timestamp (time at which JSON event is sent to output in nanoseconds).
 */
class EventData {

    @SerializedName(value = "X-Ucbrowser-Ua")
    private String ucBrowserUa;
    @SerializedName(value = "X-Ucbrowser-Device-Ua")
    private String ucBrowserDeviceUa;
    @SerializedName(value = "Accept-Language")
    private String acceptLanguage;
    @SerializedName(value = "Accept-Encoding")
    private String acceptEncoding;
    @SerializedName(value = "Accept-Charset")
    private String acceptCharset;
    @SerializedName(value = "X-Forwarded-For")
    private String xForwardedFor;
    @SerializedName(value = "Accept")
    private String accept;
    @SerializedName(value = "User-Agent")
    private String userAgent;
    @SerializedName(value = "Video_id")
    private String videoID;
    @SerializedName(value = "Clientip")
    private String clientIP;
    @SerializedName(value = "Event")
    private String event;
    @SerializedName("X-Operamini-Features")
    private String xOperaminiFeatures;
    @SerializedName("X-Operamini-Phone")
    private String xOperaminiPhone;
    @SerializedName("X-Operamini-Phone-Ua")
    private String xOperaminiPhoneUa;
    @SerializedName("Save-Data")
    private String saveData;
    @SerializedName("X-Clacks-Overhead")
    private String xClacksOverhead;
    @SerializedName("Sec-Fetch-Site")
    private String secFetchSite;
    @SerializedName("Sec-Fetch-Mode")
    private String secFetchMode;
    @SerializedName("Request-Context")
    private String requestContext;
    @SerializedName("Correlation-Context")
    private String correlationContext;
    @SerializedName("X-Ms-Request-Root-Id")
    private String xMsRequestRootID;
    @SerializedName("X-Ms-Request-Id")
    private String xMsRequestID;

    // timestamp in nanoseconds, when the event is sent to output (not in the original stream)
    @SerializedName(value = "timestamp")
    private long timestamp;

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }
}
