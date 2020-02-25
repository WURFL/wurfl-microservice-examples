using Newtonsoft.Json;
using System;

namespace event_sender
{
    class EventData
    {
        [JsonProperty("X-Ucbrowser-Ua")]
        private String ucBrowserUa;

        [JsonProperty("X-Ucbrowser-Device-Ua")]
        private String ucBrowserDeviceUa;

        [JsonProperty("Accept-Language")]
        private String acceptLanguage;

        [JsonProperty("Accept-Encoding")]
        private String acceptEncoding;

        [JsonProperty("Accept-Charset")]
        private String acceptCharset;

        [JsonProperty("X-Forwarded-For")]
        private String xForwardedFor;
        
        private String accept;

        [JsonProperty("User-Agent")]
        private String userAgent;

        [JsonProperty("Video_id")]
        private String videoID;

        [JsonProperty("Clientip")]
        private String clientIP;

        [JsonProperty("Event")]
        private String eventResult;

        [JsonProperty("X-Operamini-Features")]
        private String xOperaminiFeatures;

        [JsonProperty("X-Operamini-Phone")]
        private String xOperaminiPhone;

        [JsonProperty("X-Operamini-Phone-Ua")]
        private String xOperaminiPhoneUa;

        [JsonProperty("Save-Data")]
        private String saveData;

        [JsonProperty("X-Clacks-Overhead")]
        private String xClacksOverhead;

        [JsonProperty("Sec-Fetch-Site")]
        private String secFetchSite;

        [JsonProperty("Sec-Fetch-Mode")]
        private String secFetchMode;

        [JsonProperty("Request-Context")]
        private String requestContext;

        [JsonProperty("Correlation-Context")]
        private String correlationContext;

        [JsonProperty("X-Ms-Request-Root-Id")]
        private String xMsRequestRootID;

        [JsonProperty("X-Ms-Request-Id")]
        private String xMsRequestID;

        // timestamp in nanoseconds, when the event is sent to output (not in the original stream)
        [JsonProperty("timestamp")]
        private long timestamp;

        public void SetTimestamp(long timestamp)
        {
            this.timestamp = timestamp;
        }
    }
}