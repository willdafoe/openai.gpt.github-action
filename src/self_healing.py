import os
import openai
import json
import subprocess
import shutil
from github import Github

# Load environment variables
DEBUG_ONLY = os.getenv("DEBUG_ONLY", "true").lower() == "true"
ENABLE_ROLLBACK = os.getenv("ENABLE_ROLLBACK", "true").lower() == "true"
AUTO_MERGE = os.getenv("AUTO_MERGE", "false").lower() == "true"
PROJECT_LANGUAGE = os.getenv("LANGUAGE", "auto").lower()
RETRY_COUNT = int(os.getenv("RETRY_COUNT", "2"))  # Default: 2 retries
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
ERROR_MESSAGE = os.getenv("ERRORS")

# Function to run tests and retry if necessary
def run_tests(test_command, retry_attempts):
    for attempt in range(retry_attempts + 1):
        print(f"🧪 Running tests (Attempt {attempt + 1}/{retry_attempts + 1}): {test_command}")
        test_result = subprocess.run(test_command, shell=True, capture_output=True, text=True)

        if test_result.returncode == 0:
            return True, None  # Tests passed
        else:
            print(f"❌ Test attempt {attempt + 1} failed.")
            error_log = f"test_failure_log_{attempt + 1}.log"
            with open(error_log, "w") as log_file:
                log_file.write(test_result.stderr)

            if attempt < retry_attempts:
                print("🔄 Retrying tests...")
            else:
                return False, error_log  # Tests failed after retries

# Authenticate GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)
branch_prefix = "hotfix/" if "error" in ERROR_MESSAGE.lower() else "feature/"
branch_name = f"{branch_prefix}auto-fix-{os.getenv('GITHUB_RUN_ID')}"

# ChatGPT API call to suggest a fix
openai.api_key = OPENAI_API_KEY
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an AI that fixes code errors efficiently."},
        {"role": "user", "content": f"Fix this error:\n{ERROR_MESSAGE}"}
    ]
)

fix_suggestion = response["choices"][0]["message"]["content"]

if DEBUG_ONLY:
    issue = repo.get_issues(state="open")[0]
    issue.create_comment(f"ChatGPT suggested fix:\n\n```diff\n{fix_suggestion}\n```")
else:
    subprocess.run(["git", "checkout", "-b", branch_name])

    with open("fix_suggestion.patch", "w") as f:
        f.write(fix_suggestion)

    subprocess.run(["git", "apply", "fix_suggestion.patch"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Auto-fix applied by AI"])
    
    if TEST_COMMAND:
        test_success, log_file = run_tests(TEST_COMMAND, retry_attempts=RETRY_COUNT)

        if test_success:
            subprocess.run(["git", "push", "origin", branch_name])
            pr = repo.create_pull(
                title="AI Auto-Fix: Error Resolved",
                body=f"ChatGPT suggested fix:\n\n```diff\n{fix_suggestion}\n```\n\n✅ Tests passed.",
                head=branch_name,
                base="dev"
            )

            if AUTO_MERGE:
                pr.merge(commit_message="Auto-merged successful AI fix ✅")
                pr.create_issue_comment("✅ This fix has been successfully merged into `dev`. 🚀")
                print("✅ PR merged automatically.")

        else:
            if ENABLE_ROLLBACK:
                subprocess.run(["git", "reset", "--hard", "HEAD~1"])
                subprocess.run(["git", "push", "origin", branch_name, "--force"])
                issue.create_comment(
                    f"❌ Fix **failed tests after {RETRY_COUNT} retries**.\n\n```diff\n{fix_suggestion}\n```\n\n"
                    f"🛑 **Rollback executed.**\n📎 Test failure logs attached.\n\n"
                )
            else:
                issue.create_comment(
                    f"❌ Fix **failed tests after {RETRY_COUNT} retries** but rollback is disabled.\n\n```diff\n{fix_suggestion}\n```\n"
                    f"⚠️ Manual intervention required.\n\n📎 Test failure logs attached."
                )
    else:
        subprocess.run(["git", "push", "origin", branch_name])
        repo.create_pull(
            title="AI Auto-Fix: Error Resolved (Tests Skipped)",
            body=f"ChatGPT suggested fix:\n\n```diff\n{fix_suggestion}\n```\n\n⚠️ No tests detected, fix applied without validation.",
            head=branch_name,
            base="dev"
        )
