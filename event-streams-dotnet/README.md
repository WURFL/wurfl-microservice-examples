# event-streams-demo

Event streams demo for Wurfl Microservice is composed by two small .Net Core applications:

- sender: reads a json file containg some http request data, adds to each request entry a timestamp and sends it to the standard output

- processor: receives the http request json entries on by one from the standard input, uses WURFL microservice client to enrich them with device detection data and sends them to the standard output again.

The applications can work together passing the first one's output to the second one's input via pipe.

### Compiling and launching the demo applications 

event-streams demo requires .NET Core 2.2 or above

Clone this repository on your local machine. 

```sh
cd  event-streams-dotnet/event-processor
dotnet build
```

If compile is successful you'll read a message like:

**event-processor -> <repo_path>\event-streams-dotnet\event-processor\bin\netcoreapp2.2\event-processor.dll**

Then do

```sh
cd  ../event-sender/
dotnet build
cd bin/netcoreapp2.2/
dotnet event-sender.dll --path <path to event_stream.json> | dotnet ../../../event-processor/bin/netcoreapp2.2/event-processor.dll --host <wm server IP address>
```

- `path` is the absolute path of the event_stream.json file in your local repo. If `path` is not specified, a default value will be used. 
- If `host` is not specified, it is assumed to be `localhost`

The events-streams demo apps will output a series of data enriched Json snippets like this:

```Javascript
{
  "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
  "Accept-Encoding": "gzip, deflate, br",
  "X-Forwarded-For": "176.54.223.191",
  "User-Agent": "Mozilla/5.0 (Linux; Android 6.0.1; SM-G900FQ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.93 Mobile Safari/537.36",
  "Event": "VIDEO_OK",
  "Sec-Fetch-Site": "cross-site",
  "Sec-Fetch-Mode": "no-cors",
  "timestamp": 2541105473900,
  "Wurfl-Complete-Name": "Samsung SM-G900FQ (Galaxy S5)",
  "Wurfl-Device-OS": "Android 6.0",
  "Wurfl-Form-Factor": "Smartphone",
  "Wurfl-Device-Make": "Samsung",
  "Wurfl-Device-Model": "SM-G900FQ",
  "UserAgent": "Mozilla/5.0 (Linux; Android 6.0.1; SM-G900FQ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.93 Mobile Safari/537.36",
  "WurflCompleteName": "Samsung SM-G900FQ (Galaxy S5)",
  "WurflDeviceOS": "Android 6.0",
  "WurflDeviceMake": "Samsung",
  "WurflFormFactor": "Smartphone",
  "WurflDeviceModel": "SM-G900FQ",
  "AcceptLanguage": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
  "Timestamp": 2541105473900
}
```


**NOTES:**
- if you run this demo with WURFL Microservice for AWS/Azure you'll need to use a Standard edition or above to have access to all the capabilities used in this demo
- If you use Visual Studio (VS2017 or above is reccomended) to compile the apps, output paths may change according to the different build configuration you use (ie: Debug or Release): in that case path in the launch command must be adapted accordingly.
