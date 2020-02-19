package com.scientiamobile.wurflmicroservice.eventprocessor;

import com.google.gson.annotations.SerializedName;

/**
 * Event data class is the model for the data arriving from the JSON event stream. The only data which is added
 * during this phase if the timestamp (time at which JSON event is sent to output in nanoseconds).
 */
class EnrichedEventData {

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

    // Device detection fields
    @SerializedName("Wurfl-Complete-Name")
    private String wurflCompleteName;
    @SerializedName("Wurfl-Device-OS")
    private String wurflDeviceOS;
    @SerializedName("Wurfl-Form-Factor")
    private String wurflFormFactor;
    @SerializedName("Wurfl-Device-Make")
    private String wurflDeviceMake;
    @SerializedName("Wurfl-Device-Model")
    private String wurflDeviceModel;

    // timestamp in nanoseconds, when the event is sent to output (not in the original stream)
    @SerializedName(value = "timestamp")
    private long timestamp;


    // -------------------------------- ACCESSOR METHODS ---------------------------------------------------------------
    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    public String getUserAgent() {
        return userAgent;
    }

    public void setUserAgent(String userAgent) {
        this.userAgent = userAgent;
    }

    public String getWurflCompleteName() {
        return wurflCompleteName;
    }

    public void setWurflCompleteName(String wurflCompleteName) {
        this.wurflCompleteName = wurflCompleteName;
    }

    public String getWurflDeviceOS() {
        return wurflDeviceOS;
    }

    public void setWurflDeviceOS(String wurflDeviceOS) {
        this.wurflDeviceOS = wurflDeviceOS;
    }

    public String getWurflFormFactor() {
        return wurflFormFactor;
    }

    public void setWurflFormFactor(String wurflFormFactor) {
        this.wurflFormFactor = wurflFormFactor;
    }

    public String getWurflDeviceMake() {
        return wurflDeviceMake;
    }

    public void setWurflDeviceMake(String wurflDeviceMake) {
        this.wurflDeviceMake = wurflDeviceMake;
    }

    public String getWurflDeviceModel() {
        return wurflDeviceModel;
    }

    public void setWurflDeviceModel(String wurflDeviceModel) {
        this.wurflDeviceModel = wurflDeviceModel;
    }
}