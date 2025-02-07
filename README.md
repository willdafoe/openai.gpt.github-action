# Self-Healing GitHub Action (Now with IaC Support 🚀)

Automatically detects and fixes failing Infrastructure as Code (IaC) configurations using ChatGPT. Supports:
✅ **Terraform, Pulumi, Ansible, Packer**  
✅ **Auto-detection of IaC tools**  
✅ **Validation before merging fixes**  
✅ **Test retries before rollback**  
✅ **Auto-merging successful fixes**  

---

## **Usage**
```yaml
jobs:
  self_heal:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Self-Healing Action
        uses: your-org/self-healing-action@v1
        with:
          debug_only: false
          enable_rollback: true
          retry_count: 3
          auto_merge: true
          iac_tool: "auto"
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
