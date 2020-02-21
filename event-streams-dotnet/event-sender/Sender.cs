using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using Newtonsoft.Json;


namespace event_sender
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(Directory.GetCurrentDirectory());

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
                Console.WriteLine(JsonConvert.SerializeObject(ev));
                Thread.Sleep(100);
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
