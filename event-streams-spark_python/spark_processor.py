# SET these environment variables
# export SPARK_HOME=/opt/spark
# export PATH=$SPARK_HOME/bin:$PATH
# export PYSPARK_PYTHON=/usr/bin/python3

# Spark imports
from pyspark import SparkContext
from pyspark.streaming import StreamingContext

# WM client imports
from wmclient import WmClient

# # Other imports
import json
import argparse

# Create a local StreamingContext with two working thread and batch interval of 1 second
sc = SparkContext("local[2]", "WurflDeviceDetection")
# Duration of 1 second here
ssc = StreamingContext(sc, 10)


# Creating a client
def getOrCreateClient():
    """Gets or Creates a WM client
    """
    if "WMClient" not in globals():
        globals()["WMClient"] = WmClient.create("http", args.ip, args.port, "")

    return globals()["WMClient"]


def lookup_VM(line):
    """
    Looks up headers from the WmClient
    Args:
        line - a line from the json file
        client - WM client object
    Returns:
        dict[] containing device capabilities
    """
    evs = json.loads(line.encode().decode('utf-8-sig'))
    result = []
    for headers in evs:
        # Looks up the device details
        device = getOrCreateClient().lookup_headers(headers)

        # Error handling
        if device.error is not None and len(device.error) > 0:
            print("An error occurred: " + device.error)
            return "An error occurred: " + device.error
        else:
            result.append(device.capabilities)

    return result


def console_output(rdd):
    """
    Prints the output to the console
    Args:
        rdd - spark RDD 
    """
    brand_count = {}
    for evs in rdd:
        if isinstance(evs, str):
            print(evs)
        else:
            print("---------------------------------------------------------------------------")
            print("Complete device name: " + evs["complete_device_name"])
            print("Device OS & version:  " + evs["device_os"] + " " + evs["device_os_version"])
            print("Device form factor:    " + evs["form_factor"])
            print("---------------------------------------------------------------------------")

            if evs['brand_name'] not in brand_count:
                brand_count[evs['brand_name']] = 1
            else:
                brand_count[evs['brand_name']] += 1
    print("--------------------------------------BRAND COUNT -------------------------")
    for key in brand_count:
        print(key + ": " + str(brand_count[key]))
    print("---------------------------------------------------------------------------")


class SparkProcessor(object):
    """This class implements the spark job to process headers
    """

    def __init__(self):
        self.RECEIVER_HOST = "localhost"
        self.RECEIVER_PORT = 9999

    def main(self):
        """Main function to execute the spark job
        """
        # Create a Stream that will connect to hostname:port, like localhost:9999
        stream = ssc.socketTextStream(self.RECEIVER_HOST, self.RECEIVER_PORT)

        # Process each JSON object
        events = stream.map(lambda line: lookup_VM(line))
        events.foreachRDD(lambda rdd: rdd.foreach(console_output))

        # Start the computation
        ssc.start()
        ssc.awaitTermination()


if __name__ == '__main__':
    # Parsing command line arguments
    parser = argparse.ArgumentParser(description='WurflDeviceDetection Spark Streaming application')
    parser.add_argument('--ip', type=str, default='localhost',
                        help='IP address of the VM server')
    parser.add_argument('--port', type=int, default=80,
                        help='Port of the VM server')

    args = parser.parse_args()

    # Main thread
    spark_processor = SparkProcessor()
    spark_processor.main()
