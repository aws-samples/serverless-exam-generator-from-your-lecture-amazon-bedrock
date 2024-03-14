# Use an official Python runtime as a base image
FROM python:3.9-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the Streamlit app and Flask app into the container at /app
COPY . /app/

# Install Streamlit, Flask, and any other needed packages
RUN pip3 install --no-cache-dir streamlit boto3 flask

# Expose the ports for Streamlit and Flask apps
EXPOSE 8501 5000

# Start Streamlit and Flask

CMD sh -c 'streamlit run exam-gen.py --server.port 8501 --server.address 0.0.0.0 & python3 health.py'

