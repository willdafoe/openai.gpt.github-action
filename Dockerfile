FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the project files
COPY . /app

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set entry point to run the script
CMD ["python", "src/self_healing.py"]
