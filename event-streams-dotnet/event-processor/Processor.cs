using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using Wmclient;

namespace event_processor
{
    class Processor
    {
        static void Main(string[] args)
        {
            Console.InputEncoding = Encoding.UTF8;
            Console.OutputEncoding = Encoding.UTF8;
            var errors = new List<String>();

            String host = "localhost";
            switch (args.Length)
            {
                case 0:
                    // keeps default host
                    break;
                case 2:
                    host = args[1];
                    break;
                default:
                    Console.WriteLine("Usage: event-processor-demo [--host <WURFL microservice serve IP>]");
                    Thread.Sleep(2000);
                    Environment.Exit(1);
                    break;
            }

            WmClient wmClient = null;
            try
            {
                wmClient = WmClient.Create("http", host, "8080", "");
                wmClient.SetCacheSize(20000);
            }
            catch (WmException e)
            {
                Console.WriteLine("Unable to connect to host: " + host);
                Console.WriteLine(e.Message);
                Thread.Sleep(2000);
                Environment.Exit(1);
            }
           
            EnrichedEventData eventData = null;
            if (Console.IsInputRedirected)
            {
                using (StreamReader reader = new StreamReader(Console.OpenStandardInput(), Console.InputEncoding))
                {
                //using (var reader = new StreamReader(stream))
                //{
                    String json = reader.ReadToEnd();
                    while (json != null && json.Length > 0)
                    {
                        json = json.Trim();
                        var settings = new JsonSerializerSettings
                        {
                            MissingMemberHandling = MissingMemberHandling.Ignore,
                            NullValueHandling = NullValueHandling.Ignore,
                            StringEscapeHandling = StringEscapeHandling.EscapeNonAscii
                        };
                        eventData = JsonConvert.DeserializeObject<EnrichedEventData>(json, settings);
                        try
                        {
                            // Simulate data coming from an HTTP request
                            JSONDeviceData device = wmClient.LookupRequest(CreateRequest(eventData));
                            eventData.WurflCompleteName = device.Capabilities["complete_device_name"];
                            eventData.WurflDeviceMake = device.Capabilities["brand_name"];
                            eventData.WurflDeviceModel = device.Capabilities["model_name"];
                            eventData.WurflFormFactor = device.Capabilities["form_factor"];
                            eventData.WurflDeviceOS = device.Capabilities["device_os"] + " " + device.Capabilities["device_os_version"];

                            Console.WriteLine(JsonConvert.SerializeObject(eventData, Formatting.Indented, settings));
                            json = reader.ReadToEnd();
                        }
                        catch (WmException e)
                        {
                            Console.WriteLine(e.Message);
                            errors.Add("Cannot get device information for user-agent: " + eventData.UserAgent);
                        }
                        catch (Exception e)
                        {
                            Console.WriteLine(e.Message);
                            errors.Add("Error: " + e.Message);
                        }
                    }
                }
            }

            if (errors.Count > 0)
            {
                CreateErrorReport(errors);
            }
        }

        private static HttpRequest CreateRequest(EnrichedEventData eventData)
        {
            var request = new HttpRequestMock();
            request.Headers.Add("Accept", eventData.Accept);
            request.Headers.Add("User-Agent", eventData.UserAgent);
            request.Headers.Add("X-Ucbrowser-Device-Ua", eventData.UcBrowserDeviceUa);
            request.Headers.Add("X-Ucbrowser-Ua", eventData.UcBrowserUa);
            return request;
        }

        private static void CreateErrorReport(List<String> errors)
        {
            using (StreamWriter report = new StreamWriter(@"error_report.txt"))
            {
                foreach (string err in errors)
                {
                    report.WriteLine(err);
                }
            }
        }
    }
}

