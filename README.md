# Self-Healing GitHub Action

This action captures errors from failed GitHub Actions steps, sends them to ChatGPT, and either comments fixes or applies them in a branch.

## Features
- Captures error messages from failing steps
- Uses ChatGPT to suggest fixes
- Supports `debug_only`: 
  - `true`: Only comments on the PR with suggested fixes
  - `false`: Auto-fixes the code and opens a PR to the `dev` branch

## Usage
```yaml
- name: Self-Healing Action
  uses: your-org/self-healing-action@v1
  with:
    debug_only: false
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## License
MIT
