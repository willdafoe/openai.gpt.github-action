FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Terraform
RUN wget -O terraform.zip https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip

# Install Pulumi
RUN curl -fsSL https://get.pulumi.com | sh && \
    echo 'export PATH=$PATH:/root/.pulumi/bin' >> /etc/environment && \
    echo 'export PATH=$PATH:/root/.pulumi/bin' >> ~/.bashrc

# Install Ansible
RUN apt-get update && apt-get install -y ansible

# Install Packer
RUN wget -O packer.zip https://releases.hashicorp.com/packer/1.9.4/packer_1.9.4_linux_amd64.zip \
    && unzip packer.zip \
    && mv packer /usr/local/bin/ \
    && rm packer.zip

# Copy the entire repository
COPY . /app

# Ensure the tools are available inside the container
ENV PATH="/root/.pulumi/bin:$PATH"

# Set entry point to run the script
CMD ["python", "/app/src/self_healing.py"]
