using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using Wmclient;

namespace event_processor
{
    class Processor
    {
        static void Main(string[] args)
        {
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
            JsonSerializer serializer = new JsonSerializer();


            var inp = Console.In;
            JsonTextReader reader = new JsonTextReader(inp);
            reader.SupportMultipleContent = true;
            while (true)
            {
                if (!reader.Read())
                {
                    break;
                }
                EnrichedEventData eventData = serializer.Deserialize<EnrichedEventData>(reader);
           
                try
                {
                    // Simulate data coming from an HTTP request
                    JSONDeviceData device = wmClient.LookupRequest(CreateRequest(eventData));
                    eventData.WurflCompleteName = device.Capabilities["complete_device_name"];
                    eventData.WurflDeviceMake = device.Capabilities["brand_name"];
                    eventData.WurflDeviceModel = device.Capabilities["model_name"];
                    eventData.WurflFormFactor = device.Capabilities["form_factor"];
                    eventData.WurflDeviceOS = device.Capabilities["device_os"] + " " + device.Capabilities["device_os_version"];

                    Console.WriteLine(JsonConvert.SerializeObject(eventData));

            } catch (WmException) {
                errors.Add("Cannot get device information for user-agent: " + eventData.UserAgent);
                Thread.Sleep(10000);
            } catch (Exception e) {
                errors.Add("Error: " + e.Message);
                Thread.Sleep(10000);
                }
            if (errors.Count > 0) {
                CreateErrorReport(errors);
            }
        }
        reader.Close();
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

