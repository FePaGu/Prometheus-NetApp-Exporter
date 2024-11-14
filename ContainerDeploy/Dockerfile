# Use the official Python image from the Docker Hub
FROM python:3.12

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port that your app runs on
EXPOSE 5000

# Command to run your application
CMD ["python", "Prom_NetApp_Exporter.py"]
