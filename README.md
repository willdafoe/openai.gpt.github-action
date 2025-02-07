# Self-Healing GitHub Action

Automatically detects and fixes failing code using ChatGPT. Supports:
✅ Multi-language error detection  
✅ Automatic dependency installation  
✅ Test retries before rollback  
✅ Attaches test failure logs for debugging  
✅ Auto-merging successful fixes 🚀  

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
          auto_merge: true  # Automatically merge PRs if tests pass
          language: "auto"
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
