# Dockerfile.consumer
# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV RABBITMQ_HOST=rabbitmq
ENV POSTGRES_HOST=db
ENV POSTGRES_DB=scooters
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=adminpass

# Run consumer.py when the container launches
CMD ["python", "./consumer.py"]


# Dockerfile.producer
# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable for the RabbitMQ host
ENV RABBITMQ_HOST=rabbitmq

# Command to run the producer script
CMD ["python", "./producer.py"]
