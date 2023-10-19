# Use the official PostgreSQL image as a base
FROM postgres:latest

# Set environment variables for default username, password, and database
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=adminpass
ENV POSTGRES_DB=scooters

# Expose the default PostgreSQL port
ENV LISTEN_PORT=5432
EXPOSE 5432

# Command to run when starting the container
CMD ["postgres"]

# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages
RUN pip install --no-cache-dir flask psycopg2-binary flask_swagger_ui

# Make port 5000 available to the world outside this container
ENV LISTEN_PORT=5000
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
