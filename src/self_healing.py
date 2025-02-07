import os
import time
import openai
import json
import subprocess
import shutil
import logging
from github import Github
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
DEBUG_ONLY = os.getenv("DEBUG_ONLY", "true").lower() == "true"
ENABLE_ROLLBACK = os.getenv("ENABLE_ROLLBACK", "true").lower() == "true"
AUTO_MERGE = os.getenv("AUTO_MERGE", "false").lower() == "true"
IAC_TOOL = os.getenv("IAC_TOOL", "auto").lower()
RETRY_COUNT = int(os.getenv("RETRY_COUNT", "3"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
ERROR_MESSAGE = os.getenv("ERRORS")

# Ensure API keys are set
if not OPENAI_API_KEY or not GITHUB_TOKEN:
    logging.error("Missing required environment variables: OPENAI_API_KEY and/or GITHUB_TOKEN.")
    exit(1)

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# Function to detect Infrastructure as Code (IaC) tools
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
        "terraform": "terraform init && terraform validate",
        "pulumi": "pulumi preview",
        "ansible": "ansible-playbook --syntax-check playbook.yml",
        "packer": "packer validate .",
    }

    if iac_tool in validation_commands:
        logging.info(f"Validating {iac_tool} configuration...")
        return subprocess.run(validation_commands[iac_tool], shell=True, capture_output=True, text=True)
    return None

# Function to retry OpenAI requests on rate limit errors
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_chatgpt_fix(error_message):
    logging.info("Requesting fix from OpenAI...")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI that fixes code errors efficiently."},
            {"role": "user", "content": f"Fix this error:\n{error_message}"}
        ]
    )
    return response["choices"][0]["message"]["content"]

# Detect IaC tool if set to "auto"
if IAC_TOOL == "auto":
    IAC_TOOL = detect_iac_tool()

if IAC_TOOL == "unknown":
    logging.warning("⚠️ No supported IaC tool detected.")
    ENABLE_ROLLBACK = False

# Authenticate GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)
branch_name = f"iac-fix-{os.getenv('GITHUB_RUN_ID')}"

try:
    fix_suggestion = get_chatgpt_fix(ERROR_MESSAGE)
    logging.info("✅ Fix suggestion received from OpenAI.")

    if DEBUG_ONLY:
        issue = repo.get_issues(state="open")[0]
        issue.create_comment(f"ChatGPT suggested fix for {IAC_TOOL}:\n\n```diff\n{fix_suggestion}\n```")
    else:
        subprocess.run(["git", "checkout", "-b", branch_name])

        with open("fix_suggestion.patch", "w") as f:
            f.write(fix_suggestion)

        subprocess.run(["git", "apply", "fix_suggestion.patch"])
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", f"Auto-fix applied by AI for {IAC_TOOL}"])

        # Run validation
        validation_result = validate_iac(IAC_TOOL)

        if validation_result and validation_result.returncode == 0:
            subprocess.run(["git", "push", "origin", branch_name])
            pr = repo.create_pull(
                title=f"AI Auto-Fix: {IAC_TOOL} Configuration Resolved",
                body=f"ChatGPT suggested fix for {IAC_TOOL}:\n\n```diff\n{fix_suggestion}\n```\n\n✅ Validation passed.",
                head=branch_name,
                base="dev"
            )

            if AUTO_MERGE:
                pr.merge(commit_message=f"Auto-merged successful AI fix for {IAC_TOOL} ✅")
                pr.create_issue_comment(f"✅ This {IAC_TOOL} fix has been successfully merged into `dev`. 🚀")
                logging.info(f"✅ PR for {IAC_TOOL} merged automatically.")

        else:
            logging.error(f"❌ {IAC_TOOL} validation failed.")
            if ENABLE_ROLLBACK:
                subprocess.run(["git", "reset", "--hard", "HEAD~1"])
                subprocess.run(["git", "push", "origin", branch_name, "--force"])
                issue.create_comment(
                    f"❌ Fix **failed validation for {IAC_TOOL}**.\n\n```diff\n{fix_suggestion}\n```\n\n"
                    f"🛑 **Rollback executed.**\n📎 Validation output:\n```\n{validation_result.stderr}\n```"
                )
            else:
                issue.create_comment(
                    f"❌ Fix **failed validation for {IAC_TOOL}** but rollback is disabled.\n\n```diff\n{fix_suggestion}\n```\n"
                    f"⚠️ Manual intervention required.\n\n📎 Validation output:\n```\n{validation_result.stderr}\n```"
                )

except openai.error.RateLimitError as e:
    logging.error(f"🔥 OpenAI API rate limit exceeded: {e}")
    issue.create_comment("⚠️ OpenAI API rate limit exceeded. Please retry later.")
except openai.error.OpenAIError as e:
    logging.error(f"⚠️ OpenAI API Error: {e}")
    issue.create_comment(f"❌ OpenAI API error: {e}. Fix generation failed.")
except Exception as e:
    logging.error(f"❌ Unexpected error: {e}")
    issue.create_comment(f"❌ Unexpected error: {e}. Fix generation failed.")
