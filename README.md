# NetApp ONTAP Metrics Exporter

This Flask application serves as a metrics exporter for NetApp ONTAP storage systems. It connects to the NetApp API to retrieve metrics related to storage aggregates and volumes, formatting the data for Prometheus monitoring.

## Features

- **Metrics Retrieval**: Gathers information on storage aggregates and volumes, including:
  - Total capacity
  - Used capacity
  - Free capacity
  - IOPS (Input/Output Operations Per Second)
  - Latency
  - Throughput
- **Prometheus Compatibility**: Outputs metrics in a format compatible with Prometheus, allowing easy integration with monitoring systems.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/repository-name.git
   cd repository-name

2. **Install Dependencies**:
   
   Make sure you have Python 3.x installed. Then, install the required packages:
   ```bash
   pip install Flask netapp_ontap

3. **Set Environment Variables**:
   
   Set the following environment variables with your NetApp ONTAP credentials:
   ```bash
   export NETAPP_IP='your_netapp_ip'
   export NETAPP_USERNAME='your_username'
   export NETAPP_PASSWORD='your_password'

## Usage

   Run the application using:
   ```bash
   python app.py
   ```

   The application will start and listen on port 5000. You can access the metrics at:
   ```bash
   http://localhost:5000/metrics
   ```

## Example Output

The /metrics endpoint will return data formatted for Prometheus, including metrics for aggregates and volumes.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features you would like to see.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
