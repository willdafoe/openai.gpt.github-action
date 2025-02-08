FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Pulumi inside the container
RUN curl -fsSL https://get.pulumi.com | sh && \
    echo 'export PATH=$PATH:/root/.pulumi/bin' >> /etc/environment && \
    echo 'export PATH=$PATH:/root/.pulumi/bin' >> ~/.bashrc

# Copy the entire repository
COPY . /app

# Set entry point to run the script
CMD ["python", "/app/src/self_healing.py"]
