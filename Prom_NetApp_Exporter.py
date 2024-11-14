from flask import Flask, Response  # Import Flask for web framework and Response for HTTP responses
import os  # Import os for environment variable access
from netapp_ontap import HostConnection, config  # Import necessary classes from the NetApp ONTAP SDK
from netapp_ontap.resources import Aggregate, Volume  # Import Aggregate and Volume resources
from netapp_ontap.error import NetAppRestError  # Import error handling for NetApp REST API

app = Flask("PromNetAppExporter") # Initialize the Flask application

def connect_to_netapp(netapp_ip, username, password):
    # Create a connection to the NetApp ONTAP system
    conn = HostConnection(netapp_ip, username=username, password=password, verify=False)
    config.CONNECTION = conn  # Set the global connection configuration
    return conn  # Return the connection object

def get_aggregates():
    try:
        # Retrieve a collection of aggregates with specified fields
        aggregates = Aggregate.get_collection(fields="home_node.name,node.uuid,metric.iops.total,metric.iops.read,"
                                                     "metric.iops.write,metric.latency.total,metric.latency.read,"
                                                     "metric.latency.write,metric.throughput.total,"
                                                     "metric.throughput.read,metric.throughput.write,"
                                                     "space.block_storage.size,name,node.name,"
                                                     "space.block_storage.used,space.block_storage.available")
        return aggregates  # Return the list of aggregates
    except NetAppRestError as e:
        app.logger.error(f"Error retrieving aggregates: {e}")  # Log any errors encountered
        return None  # Return None if there was an error

def get_volumes():
    try:
        # Retrieve a collection of volumes with specified fields
        volumes = Volume.get_collection(fields="aggregates.uuid,aggregates.name,svm,space,"
                                                "metric.iops.total,metric.iops.read,"
                                                "metric.iops.write,metric.latency.total,"
                                                "metric.latency.read,metric.latency.write,"
                                                "metric.throughput.total,metric.throughput.read,"
                                                "metric.throughput.write")
        return volumes  # Return the list of volumes
    except NetAppRestError as e:
        app.logger.error(f"Error retrieving volumes: {e}")  # Log any errors encountered
        return None  # Return None if there was an error

@app.route('/metrics', methods=['GET'])  # Define an endpoint for metrics retrieval
def metrics():
    netapp_ip = os.getenv('NETAPP_IP')  # Get NetApp IP from environment variable
    username = os.getenv('NETAPP_USERNAME')  # Get username from environment variable
    password = os.getenv('NETAPP_PASSWORD')  # Get password from environment variable

    if not netapp_ip or not username or not password:  # Check for missing environment variables
        return Response("Missing required environment variables", status=400)  # Return error response

    conn = connect_to_netapp(netapp_ip, username, password)  # Connect to NetApp ONTAP
    aggregates = get_aggregates()  # Retrieve aggregates
    volumes = get_volumes()  # Retrieve volumes

    if aggregates is None or volumes is None:  # Check if retrieval was successful
        return Response("Failed to retrieve aggregates or volumes", status=500)  # Return error response

    prometheus_output = []  # Initialize a list to hold Prometheus formatted output

    # Aggregate metrics section
    prometheus_output.append("# HELP netapp_aggregate_names List of storage aggregates")  # Help text for Prometheus
    prometheus_output.append("# TYPE netapp_aggregate_names gauge")  # Metric type declaration

    for aggregate in aggregates:  # Loop through each aggregate to gather metrics
        uuid = aggregate.uuid  # Get the UUID of the aggregate
        prometheus_output.append(f"netapp_aggregate{{aggregate=\"{uuid}\"}} 1")  # Metric existence indicator

        name = aggregate.name.replace(" ", "_")  # Replace spaces in names with underscores for metric names
        prometheus_output.append(f"netapp_aggregate_names{{aggregate=\"{uuid}\",name=\"{name}\"}} 1")  # Aggregate name metric

        nodename = aggregate.node.name.replace(" ", "_")
        prometheus_output.append(f"netapp_aggregate_node_names{{aggregate=\"{uuid}\",node=\"{nodename}\"}} 1")

        uuidnodo = aggregate.node.uuid
        prometheus_output.append(f"netapp_aggregate_node{{aggregate=\"{uuid}\",node=\"{uuidnodo}\"}} 1")

        capacity = (aggregate.space.block_storage.size / 1.1e+12)
        prometheus_output.append(f"netapp_aggregate_total_capacity{{aggregate=\"{uuid}\"}} {capacity}")

        capacityused = (aggregate.space.block_storage.used / 1.1e+12)
        prometheus_output.append(f"netapp_aggregate_used_capacity{{aggregate=\"{uuid}\"}} {capacityused}")

        capacityavailable = (aggregate.space.block_storage.available / 1.1e+12)
        prometheus_output.append(f"netapp_aggregate_free_capacity{{aggregate=\"{uuid}\"}} {capacityavailable}")

        # New metrics for IOPS (Input/Output Operations Per Second), latency, and throughput
        iops_total = aggregate.metric.iops.total
        prometheus_output.append(f"netapp_aggregate_iops_total{{aggregate=\"{uuid}\"}} {iops_total}")

        iops_read = aggregate.metric.iops.read
        prometheus_output.append(f"netapp_aggregate_iops_read{{aggregate=\"{uuid}\"}} {iops_read}")

        iops_write = aggregate.metric.iops.write
        prometheus_output.append(f"netapp_aggregate_iops_write{{aggregate=\"{uuid}\"}} {iops_write}")

        latency_total = aggregate.metric.latency.total
        prometheus_output.append(f"netapp_aggregate_latency_total{{aggregate=\"{uuid}\"}} {latency_total}")

        latency_read = aggregate.metric.latency.read
        prometheus_output.append(f"netapp_aggregate_latency_read{{aggregate=\"{uuid}\"}} {latency_read}")

        latency_write = aggregate.metric.latency.write
        prometheus_output.append(f"netapp_aggregate_latency_write{{aggregate=\"{uuid}\"}} {latency_write}")

        throughput_total = aggregate.metric.throughput.total
        prometheus_output.append(f"netapp_aggregate_throughput_total{{aggregate=\"{uuid}\"}} {throughput_total}")

        throughput_read = aggregate.metric.throughput.read
        prometheus_output.append(f"netapp_aggregate_throughput_read{{aggregate=\"{uuid}\"}} {throughput_read}")

        throughput_write = aggregate.metric.throughput.write
        prometheus_output.append(f"netapp_aggregate_throughput_write{{aggregate=\"{uuid}\"}} {throughput_write}")

    # Volume metrics section (similar structure as above)
    prometheus_output.append("# HELP netapp_volume_names List of storage volumes")
    prometheus_output.append("# TYPE netapp_volume_names gauge")

    for volume in volumes:
        uuid = volume.uuid
        prometheus_output.append(f"netapp_volume{{volume=\"{uuid}\"}} 1")

        name = volume.name.replace(" ", "_")
        prometheus_output.append(f"netapp_volume_names{{volume=\"{uuid}\",name=\"{name}\"}} 1")

        svmuuid = volume.svm.uuid
        prometheus_output.append(f"netapp_volume_svm{{volume=\"{uuid}\",svm=\"{svmuuid}\"}} 1")

        svmname = volume.svm.name.replace(" ", "_")
        prometheus_output.append(f"netapp_volume_svm_names{{volume=\"{uuid}\",svm_name=\"{svmname}\"}} 1")

        if volume.aggregates:
            agguuid = [agg.uuid for agg in volume.aggregates]
            aggu = ",".join(agguuid)
            aggname = [agg.name.replace(" ","_") for agg in volume.aggregates]
            aggn = ",".join(aggname)
        else:
            aggn = "none"

        prometheus_output.append(f"netapp_volume_aggregates{{volume=\"{uuid}\",aggregate=\"{aggu}\"}} 1")
        prometheus_output.append(f"netapp_volume_aggregates_names{{volume=\"{uuid}\",aggregate_name=\"{aggn}\"}} 1")

        total_capacity = (volume.space.size / 1.1e+12)
        prometheus_output.append(f"netapp_volume_total_capacity{{volume=\"{uuid}\"}} {total_capacity}")

        used_capacity = (volume.space.used / 1.1e+12)
        prometheus_output.append(f"netapp_volume_used_capacity{{volume=\"{uuid}\"}} {used_capacity}")

        free_capacity = (volume.space.available / 1.1e+12)
        prometheus_output.append(f"netapp_volume_free_capacity{{volume=\"{uuid}\"}} {free_capacity}")

        vol_iops_total = volume.metric.iops.total
        prometheus_output.append(f"netapp_volume_iops_total{{volume=\"{uuid}\"}} {iops_total}")

        vol_iops_read = volume.metric.iops.read
        prometheus_output.append(f"netapp_volume_iops_read{{volume=\"{uuid}\"}} {iops_read}")

        vol_iops_write = volume.metric.iops.write
        prometheus_output.append(f"netapp_volume_iops_write{{volume=\"{uuid}\"}} {iops_write}")

        vol_latency_total = volume.metric.latency.total
        prometheus_output.append(f"netapp_volume_latency_total{{volume=\"{uuid}\"}} {latency_total}")

        vol_latency_read = volume.metric.latency.read
        prometheus_output.append(f"netapp_volume_latency_read{{volume=\"{uuid}\"}} {latency_read}")

        vol_latency_write = volume.metric.latency.write
        prometheus_output.append(f"netapp_volume_latency_write{{volume=\"{uuid}\"}} {latency_write}")

        vol_throughput_total = volume.metric.throughput.total
        prometheus_output.append(f"netapp_volume_throughput_total{{volume=\"{uuid}\"}} {throughput_total}")

        vol_throughput_read = volume.metric.throughput.read
        prometheus_output.append(f"netapp_volume_throughput_read{{volume=\"{uuid}\"}} {throughput_read}")

        vol_throughput_write = volume.metric.throughput.write
        prometheus_output.append(f"netapp_volume_throughput_write{{volume=\"{uuid}\"}} {throughput_write}")

    return Response("\n".join(prometheus_output) + "\n", content_type='text/plain')

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000)   # Run the Flask application on all interfaces at port 5000
