import os
import openai
import json
import subprocess
from github import Github

# Load environment variables
DEBUG_ONLY = os.getenv("DEBUG_ONLY", "true").lower() == "true"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
ERROR_MESSAGE = os.getenv("ERRORS")

# Authenticate GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)
branch_prefix = "hotfix/" if "error" in ERROR_MESSAGE.lower() else "feature/"
branch_name = f"{branch_prefix}auto-fix-{os.getenv('GITHUB_RUN_ID')}"

# ChatGPT API call
openai.api_key = OPENAI_API_KEY
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an AI code fixer."},
        {"role": "user", "content": f"Fix this error:\n{ERROR_MESSAGE}"}
    ]
)

fix_suggestion = response["choices"][0]["message"]["content"]

if DEBUG_ONLY:
    # Just comment on the PR
    issue = repo.get_issues(state="open")[0]  # Modify to get correct PR
    issue.create_comment(f"ChatGPT suggested fix:\n\n{fix_suggestion}")
else:
    # Apply fix
    subprocess.run(["git", "checkout", "-b", branch_name])
    with open("fix_suggestion.txt", "w") as f:
        f.write(fix_suggestion)

    subprocess.run(["git", "commit", "-am", "Auto-fix applied by AI"])
    subprocess.run(["git", "push", "origin", branch_name])

    # Create a pull request
    repo.create_pull(
        title="AI Auto-Fix: Error Resolved",
        body=f"ChatGPT suggested fix:\n\n{fix_suggestion}",
        head=branch_name,
        base="dev"
    )
