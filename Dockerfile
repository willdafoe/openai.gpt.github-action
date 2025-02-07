FROM python:3.10

WORKDIR /app

# Copy all required files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the entry point to run the script
CMD ["python", "/app/src/self_healing.py"]
