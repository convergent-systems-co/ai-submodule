# GitHub Pages Setup Guide

This guide covers enabling GitHub Pages for your project using the same MkDocs Material theme and workflow used by the Dark Forge documentation site.

## Prerequisites

- A GitHub repository with the Dark Forge submodule (`.ai/`) configured
- Repository admin access (to enable GitHub Pages)
- Python 3.12+ (for local preview)

## 1. Enable GitHub Pages in Repository Settings

1. Navigate to your repository on GitHub
2. Go to **Settings > Pages**
3. Under **Source**, select **GitHub Actions**
4. Save

This tells GitHub to deploy pages from a GitHub Actions workflow rather than a branch.

## 2. Add the Deploy Workflow

Create `.github/workflows/deploy-docs.yml` in your repository. Dark Forge ships a reference workflow you can copy directly:

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
      - '.github/workflows/deploy-docs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install MkDocs and dependencies
        run: |
          pip install mkdocs-material pymdown-extensions

      - name: Build documentation
        run: mkdocs build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site/

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

This workflow:
- Triggers on pushes to `main` that touch `docs/`, `mkdocs.yml`, or the workflow itself
- Supports manual dispatch via `workflow_dispatch`
- Builds the site with MkDocs Material
- Deploys to GitHub Pages using the official `deploy-pages` action

## 3. Configure MkDocs

Create `mkdocs.yml` in your repository root. Use this minimal configuration to match the Dark Forge theme:

```yaml
site_name: My Project Documentation
site_description: Project documentation
site_url: https://your-org.github.io/your-repo
repo_url: https://github.com/your-org/your-repo
repo_name: your-org/your-repo

theme:
  name: material
  palette:
    scheme: default
    primary: indigo
    accent: indigo
  icon:
    repo: fontawesome/brands/github
  features:
    - navigation.top
    - navigation.sticky
    - navigation.indexes
    - navigation.footer
    - search.suggest
    - search.highlight
    - content.code.copy
    - toc.integrate

markdown_extensions:
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tabbed:
      alternate_style: true
  - admonition
  - pymdownx.details
  - attr_list
  - md_in_html
  - tables
  - toc:
      permalink: true

plugins:
  - search

nav:
  - Home: index.md
```

### Using the Nord Theme (Same as Dark Forge)

To match the Dark Forge site exactly, use the Nord color scheme. Add a custom stylesheet:

1. Create `docs/stylesheets/extra.css`:

```css
[data-md-color-scheme="nord"] {
  --md-primary-fg-color: #5e81ac;
  --md-accent-fg-color: #88c0d0;
}
```

2. Update `mkdocs.yml`:

```yaml
theme:
  palette:
    scheme: nord
    primary: custom
    accent: custom

extra_css:
  - stylesheets/extra.css
```

## 4. Add Documentation Content

Create the `docs/` directory and add your content:

```
docs/
  index.md          # Home page (required)
  guides/
    getting-started.md
  architecture/
    overview.md
```

### Minimal `docs/index.md`

```markdown
# My Project

Welcome to the project documentation.

## Quick Start

See the [Getting Started](guides/getting-started.md) guide.
```

## 5. Configure project.yaml

Add the `github_pages` flag to your `project.yaml` so the governance framework knows Pages is enabled:

```yaml
github_pages:
  enabled: true
  theme: "material"
  url: "https://your-org.github.io/your-repo"
```

## 6. Local Preview

Preview the site locally before pushing:

```bash
# Install dependencies
pip install mkdocs-material pymdown-extensions

# Serve locally with live reload
mkdocs serve

# Open http://127.0.0.1:8000 in your browser
```

## 7. Verify Deployment

After pushing to `main`:

1. Go to the **Actions** tab in your repository
2. Confirm the "Deploy Documentation" workflow ran successfully
3. Navigate to **Settings > Pages** to find your site URL
4. Visit `https://your-org.github.io/your-repo`

## Adding Mermaid Diagrams

To render Mermaid diagrams in your documentation, add the Mermaid JavaScript dependency. Dark Forge self-hosts Mermaid v11.3.0 to eliminate CDN supply-chain risk. For your project, you can either:

**Option A: Use the CDN (simpler)**

```yaml
# mkdocs.yml
extra_javascript:
  - https://unpkg.com/mermaid@11/dist/mermaid.min.js

markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_div_format
```

**Option B: Self-host (recommended for production)**

Copy the Mermaid files from the Dark Forge submodule:

```bash
cp .ai/docs/javascripts/mermaid.min.js docs/javascripts/
cp .ai/docs/javascripts/mermaid-init.js docs/javascripts/
```

Then reference them in `mkdocs.yml`:

```yaml
extra_javascript:
  - javascripts/mermaid.min.js
  - javascripts/mermaid-init.js
```

## Troubleshooting

### Build fails with "Config file not found"

Ensure `mkdocs.yml` is in the repository root (not inside `docs/`).

### Pages shows 404

- Verify GitHub Pages source is set to **GitHub Actions** (not a branch)
- Confirm the workflow completed successfully in the Actions tab
- Check that `docs/index.md` exists

### Styles do not match Dark Forge

Ensure you are using `mkdocs-material` (not the base `mkdocs` theme) and have the `pymdownx` extensions installed.
