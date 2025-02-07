import os
import subprocess
import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
IAC_TOOL = os.getenv("IAC_TOOL", "auto").lower()

# Initialize OpenAI client (NEW API)
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

# Function to retry OpenAI requests on rate limits
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_chatgpt_fix(error_message):
    logging.info("Requesting fix from OpenAI...")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI that fixes IaC errors efficiently."},
                {"role": "user", "content": f"Fix this error:\n{error_message}"}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return None

# Function to detect IaC tool
def detect_iac_tool():
    if os.path.exists("main.tf") or os.path.exists(".terraform"):
        return "terraform"
    elif os.path.exists("Pulumi.yaml") or os.path.exists("index.ts") and "pulumi" in open("index.ts").read():
        return "pulumi"
    elif os.path.exists("ansible.cfg") or os.path.exists("playbook.yml"):
        return "ansible"
    elif os.path.exists("packer.json") or os.path.exists("packer.pkr.hcl"):
        return "packer"
    return "unknown"

# Function to validate IaC configurations
def validate_iac(iac_tool):
    validation_commands = {
        "terraform": "terraform fmt -check && terraform validate",
        "pulumi": "pulumi preview",
        "ansible": "ansible-lint && ansible-playbook --syntax-check playbook.yml",
        "packer": "packer validate .",
    }

    if iac_tool in validation_commands:
        logging.info(f"🔍 Running validation checks for {iac_tool}...")
        result = subprocess.run(validation_commands[iac_tool], shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info(f"✅ {iac_tool} validation passed.")
            return True
        else:
            logging.error(f"❌ {iac_tool} validation failed:\n{result.stderr}")
            return result.stderr  # Return the error message for AI fix suggestion
    return None

# Function to deploy IaC if validation passes
def deploy_iac(iac_tool):
    deployment_commands = {
        "terraform": "terraform apply -auto-approve",
        "pulumi": "pulumi up --yes",
        "ansible": "ansible-playbook playbook.yml",
        "packer": "packer build .",
    }

    if iac_tool in deployment_commands:
        logging.info(f"🚀 Deploying infrastructure using {iac_tool}...")
        result = subprocess.run(deployment_commands[iac_tool], shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            logging.info(f"✅ {iac_tool} deployment successful.")
        else:
            logging.error(f"❌ {iac_tool} deployment failed:\n{result.stderr}")

# Detect IaC tool if set to "auto"
if IAC_TOOL == "auto":
    IAC_TOOL = detect_iac_tool()

if IAC_TOOL == "unknown":
    logging.warning("⚠️ No supported IaC tool detected.")
    exit(1)

# Run validation checks
validation_result = validate_iac(IAC_TOOL)

if validation_result is True:
    # If validation passes, proceed with deployment
    deploy_iac(IAC_TOOL)
elif validation_result:
    # If validation fails, request AI-generated fixes
    fix_suggestion = get_chatgpt_fix(validation_result)
    if fix_suggestion:
        logging.info(f"🤖 AI Suggested Fix:\n{fix_suggestion}")
    else:
        logging.error("❌ AI was unable to generate a fix.")
