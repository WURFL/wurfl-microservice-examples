using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text;

namespace event_processor
{
    class EnrichedEventData
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

        [JsonProperty("Accept")]
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

        // Device detection fields
        [JsonProperty("Wurfl-Complete-Name")]
        private String wurflCompleteName;
        [JsonProperty("Wurfl-Device-OS")]
        private String wurflDeviceOS;
        [JsonProperty("Wurfl-Form-Factor")]
        private String wurflFormFactor;
        [JsonProperty("Wurfl-Device-Make")]
        private String wurflDeviceMake;
        [JsonProperty("Wurfl-Device-Model")]
        private String wurflDeviceModel;

        // Accessor properties
        public string UserAgent { get => userAgent; set => userAgent = value; }
        public string WurflCompleteName { get => wurflCompleteName; set => wurflCompleteName = value; }
        public string WurflDeviceOS { get => wurflDeviceOS; set => wurflDeviceOS = value; }
        public string WurflDeviceMake { get => wurflDeviceMake; set => wurflDeviceMake = value; }
        public string WurflFormFactor { get => wurflFormFactor; set => wurflFormFactor = value; }
        public string WurflDeviceModel { get => wurflDeviceModel; set => wurflDeviceModel = value; }
        public string UcBrowserUa { get => ucBrowserUa; set => ucBrowserUa = value; }
        public string UcBrowserDeviceUa { get => ucBrowserDeviceUa; set => ucBrowserDeviceUa = value; }
        public string AcceptLanguage { get => acceptLanguage; set => acceptLanguage = value; }
        public string Accept { get => accept; set => accept = value; }
        public string XOperaminiPhoneUa { get => xOperaminiPhoneUa; set => xOperaminiPhoneUa = value; }
    }
}
