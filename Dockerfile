FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy all files into the container
COPY . /app

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set entry point to run Python script
CMD ["python", "src/self_healing.py"]
