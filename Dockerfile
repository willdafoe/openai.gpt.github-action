# 🏗 Base Image: Python 3.10
FROM python:3.10 AS base

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Install Ansible manually inside the container
RUN apt-get update && apt-get install -y ansible

# 🏗 Stage 2: Add Terraform from HashiCorp’s Official Image
FROM hashicorp/terraform:1.6.0 AS terraform

# 🏗 Stage 3: Add Pulumi from Pulumi’s Official Image
FROM pulumi/pulumi:latest AS pulumi

# 🏗 Stage 4: Add Packer from HashiCorp’s Official Image
FROM hashicorp/packer:1.9.4 AS packer

# 🏗 Final Image: Combine All Layers
FROM base AS final

# Copy binaries from Terraform, Pulumi, and Packer layers
COPY --from=terraform /bin/terraform /usr/local/bin/terraform
COPY --from=pulumi /usr/bin/pulumi /usr/local/bin/pu
COPY --from=packer /bin/packer /usr/local/bin/packer

# Copy the entire repository into the final image
COPY . /app

# Ensure paths are correctly set for Pulumi
ENV PATH="/root/.pulumi/bin:$PATH"

# Set entry point to run the self-healing script
CMD ["python", "/app/src/self_healing.py"]
