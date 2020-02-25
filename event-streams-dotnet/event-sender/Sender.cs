﻿using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace event_sender
{
    class Program
    {
        static void Main(string[] args)
        {
            var path = @"..\..\..\event_stream.json";
            // This text is added only once to the file.
            if (!File.Exists(path))
            {
                Console.WriteLine("Unable to open json event stream, file does not exist");
                Thread.Sleep(2000);
                Environment.Exit(1);
            }
            var json = File.ReadAllText(path);
            var events = JsonConvert.DeserializeObject<EventData[]>(json);
            foreach(EventData ev in events)
            {
                // Adds a timestamp, serializes events again and sends it to the stdout one by one
                ev.SetTimestamp(GetTimestamp());
                JsonSerializerSettings settings = new JsonSerializerSettings
                {
                    NullValueHandling = NullValueHandling.Ignore,
                    StringEscapeHandling = StringEscapeHandling.EscapeNonAscii
                    
                };
                var njson = JsonConvert.SerializeObject(ev, settings);
                var jsonFormatted = JValue.Parse(njson).ToString(Formatting.Indented);
                Console.OutputEncoding = Encoding.UTF8;
                Console.Write(jsonFormatted);
                Console.Out.Flush();
                //Console.Out.Close();
                Thread.Sleep(200);
            }

        }

        // gets a timestamp in nanoseconds
        static long GetTimestamp()
        {
            var timestamp = Stopwatch.GetTimestamp();
            var nanoseconds = 1_000_000_000.0 * timestamp / Stopwatch.Frequency;

            return (long) nanoseconds;
        }
    }
}
