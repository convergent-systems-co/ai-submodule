---
agent: agent
model: Claude Sonnet 4.5 (copilot)
name: global-ops-github-pages-setup
description: Sets up GitHub Pages on a repository using GitHub Actions deployment with Jekyll 4.x. Includes workflow creation, Jekyll configuration, Liquid template protection, and optional URL migration.
status: beta
tags: ['github-pages', 'deployment', 'documentation', 'workflow', 'jekyll']
---

# GitHub Pages Setup and Configuration

## Purpose

Systematically enable GitHub Pages on a repository, with support for:

- **New Setup**: Fresh GitHub Pages deployment
- **Migration**: Updating URLs from a source repo's Pages to the new repo's Pages

## Prerequisites

- `gh` CLI authenticated with access to the target repository
- Repository must have a `docs/` folder (or specify alternate path)
- Branch with content must exist on the remote before enabling Pages

## Process

### Step 1: Determine Mode

Ask the user:

```
Is this a new GitHub Pages setup or a migration from an existing repo?

A) New Setup - Fresh deployment, no URL changes needed
B) Migration - Need to update URLs from source repo's Pages
```

**If Migration**, also ask:

- What is the source repo's GitHub Pages URL pattern? (e.g., `symmetrical-adventure-6l6zq4m.pages.github.io`)

### Step 2: Verify Branch is Pushed

GitHub Pages can only be configured for branches that exist on the remote.

```bash
# Check if current branch exists on remote
BRANCH=$(git branch --show-current)
git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH" || echo "Branch not pushed yet"
```

If not pushed:

```bash
git push origin "$BRANCH"
```

### Step 3: Check Current Pages Status

```bash
# Check if Pages is already configured
gh api repos/{owner}/{repo}/pages 2>&1 || echo "Pages not configured"
```

### Step 4: Configure Pages Source as GitHub Actions

GitHub Pages must use **GitHub Actions** as the deployment source (not "Deploy from a branch"). This enables Jekyll 4.x support with `render_with_liquid: false` front matter.

Change in repo settings: **Settings → Pages → Source → GitHub Actions**

### Step 5: Create Pages Workflow

Create `.github/workflows/pages.yml`:

```yaml
# Deploy GitHub Pages with Jekyll 4.x
#
# This workflow builds and deploys the docs site using Jekyll 4.x via GitHub Actions,
# enabling render_with_liquid: false front matter support.
#
# Replaces the legacy GitHub Pages build (Jekyll 3.9.3).
#
# See: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow

name: Deploy GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - '.github/workflows/pages.yml'

  # Allow manual trigger
  workflow_dispatch:

# Sets permissions of the GITHUB_TOKEN
permissions:
  contents: read
  pages: write
  id-token: write

# Allow only one concurrent deployment
concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
          working-directory: docs
          bundler-cache: true

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Build Jekyll site
        working-directory: docs
        run: bundle exec jekyll build --baseurl "${{ steps.pages.outputs.base_path }}"
        env:
          JEKYLL_ENV: production

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/_site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Step 6: Create Jekyll Configuration Files

Create `docs/Gemfile`:

```ruby
source "https://rubygems.org"

gem "jekyll", "~> 4.3"
gem "webrick"  # Required for Ruby 3.x local server
```

Create `docs/_config.yml`:

```yaml
title: <Project Name>
description: <Project description>
baseurl: "/<repo-name>"
url: "https://<org>.github.io"

markdown: kramdown
highlighter: rouge

exclude:
  - Gemfile
  - Gemfile.lock
  - README.md
  - vendor

kramdown:
  input: GFM
  hard_wrap: false
  syntax_highlighter: rouge
```

### Step 7: Protect Docs with Liquid Template Expressions

Documentation files containing template expressions (`${{ }}` for GitHub Actions, `{{ }}` for Go/Helm templates) will break Jekyll builds.

**Preferred approach** — add to front matter of affected files:

```yaml
---
render_with_liquid: false
---
```

**Alternative** (for files that need partial Liquid processing):

```
{% raw %}
... template expressions here ...
{% endraw %}
```

Scan for files that need protection:

```bash
find docs -name "*.md" -type f -exec grep -l -E '(\$\{\{|\{\{[^%])' {} \;
```

### Step 8: Optional - Add Lint Workflow

Create `.github/workflows/lint-docs-liquid.yml` to catch unprotected template expressions:

```yaml
name: Lint Docs for Liquid Syntax

on:
  pull_request:
    paths:
      - 'docs/**/*.md'

jobs:
  check-liquid-syntax:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for unwrapped template expressions
        run: |
          echo "Checking for unwrapped template expressions in docs/..."
          ERRORS=0
          while IFS= read -r -d '' file; do
            if grep -qE '(\$\{\{|\{\{[^%])' "$file"; then
              if grep -q 'render_with_liquid: false' "$file" || grep -q '{% raw %}' "$file"; then
                continue
              fi
              echo "❌ $file: Contains template expressions but no protection"
              ERRORS=$((ERRORS + 1))
            fi
          done < <(find docs -name "*.md" -type f -print0)
          if [ "$ERRORS" -gt 0 ]; then
            echo "::error::Found $ERRORS file(s) with unprotected expressions."
            exit 1
          fi
          echo "✅ All docs properly protected"
```

### Step 9: Migration Only - Update URLs

**Skip this step for new setups.**

For migrations, find and replace all source repo URLs with the new URLs:

```bash
# Find files with old URLs
OLD_URL="<source-pages-url>"  # e.g., symmetrical-adventure-6l6zq4m.pages.github.io
NEW_URL="<new-pages-url>"      # e.g., stunning-adventure-zrj6g8l.pages.github.io

# Count occurrences
grep -r "$OLD_URL" --include="*.md" --include="*.html" --include="*.json" -c | grep -v ":0$"

# Replace all occurrences
find . -type f \( -name "*.md" -o -name "*.html" -o -name "*.json" \) \
  -exec grep -l "$OLD_URL" {} \; | \
  xargs sed -i '' "s/${OLD_URL//./\\.}/${NEW_URL}/g"

# Verify replacement
echo "Old URLs remaining: $(grep -r "$OLD_URL" --include="*.md" --include="*.html" --include="*.json" | wc -l)"
echo "New URLs now: $(grep -r "$NEW_URL" --include="*.md" --include="*.html" --include="*.json" | wc -l)"
```

### Step 10: Verify Deployment

Wait for the GitHub Actions workflow to complete:

```bash
# Check build status
gh api repos/{owner}/{repo}/pages/builds --jq '.[0] | "\(.status) at \(.created_at)"'
```

For **public repos**:

```bash
curl -s -o /dev/null -w "%{http_code}" "https://<new-pages-url>/index.html"
# Should return 200
```

For **private/internal repos**:

```
⚠️ Private repo - manual verification required.
Please open in browser: https://<new-pages-url>/
```

## Summary Output

Report to user:

```
✅ GitHub Pages Setup Complete

Mode: [New Setup / Migration]
Pages URL: https://<pages-url>/
Branch: <branch-name>
Publish Path: /docs

[Migration only]
URLs Updated: X occurrences in Y files
Source: <old-url>
Target: <new-url>

Next Steps:
1. ✅ Pages workflow created
2. ✅ Jekyll configuration set up
3. ✅ Liquid template protection applied
4. → Merge to main to trigger first deployment
5. → Verify Pages are accessible after deployment
```

## Troubleshooting

### Pages API returns 404

- Ensure you have admin access to the repository
- Check repository visibility settings allow Pages

### Build fails

```bash
# Check build error
gh api repos/{owner}/{repo}/pages/builds --jq '.[0]'
```

Common issues:

- Missing index.html in docs folder
- Invalid HTML/Jekyll syntax
- Large files exceeding limits
- Unprotected Liquid template expressions (see Step 7)

### Private repo Pages not accessible

- Verify you're authenticated in browser
- Check org settings allow private Pages
- Enterprise/Team plan required for private Pages

### URL replacement missed some files

```bash
# Search all files (not just md/html/json)
grep -r "<old-url>" .
```

Add additional file extensions to the find command as needed.

## References

- [ADR 016: Jekyll 4.x Upgrade](docs/adr/016-jekyll-4-upgrade-render-with-liquid.md)
- [Writing Docs with Template Expressions](docs/guides/writing-docs-with-template-expressions.md)
- [GitHub Pages Publishing Source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

## Integration with Other Prompts

This prompt pairs well with:

- `global-dev-pr-create` - Create PR after Pages setup
- `global-dev-git-review` - Commit changes properly before push

## Notes

- GitHub Pages URLs follow pattern: `https://<random-codename>.pages.github.io/`
- The codename is assigned by GitHub and cannot be customized (unless using custom domain)
- Build history is available via API for debugging
- For orgs with many repos, consider documenting the Pages URL mapping
- Jekyll 4.x is required for `render_with_liquid: false` support (GitHub's built-in Pages uses Jekyll 3.9.3)
