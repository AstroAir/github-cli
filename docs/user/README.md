# User Guide

Welcome to GitHub CLI! This comprehensive guide will help you get started and make the most of the advanced terminal-based GitHub client.

## 🚀 Getting Started

### Installation

#### From Source (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/github-cli.git
cd github-cli

# Install the package
pip install -e .
```

#### Using pip (when available)
```bash
pip install github-cli
```

#### Verify Installation
```bash
github-cli --version
github-cli --help
```

### First Time Setup

1. **Authentication**
   ```bash
   github-cli auth login
   ```
   This will start the OAuth device flow and guide you through authentication.

2. **Check Status**
   ```bash
   github-cli auth status
   ```

3. **Launch TUI (Optional)**
   ```bash
   github-cli tui
   ```

## 🔐 Authentication

### OAuth Device Flow

GitHub CLI uses OAuth device flow for secure authentication:

1. **Start Authentication**
   ```bash
   github-cli auth login
   ```

2. **Follow Instructions**
   - A browser will open (or you'll get a URL to visit)
   - Enter the provided device code
   - Authorize the application

3. **Verify Authentication**
   ```bash
   github-cli auth status
   ```

### Authentication Options

```bash
# Login with specific scopes
github-cli auth login --scopes "repo,user,gist,workflow"

# Login for organization with SSO
github-cli auth login --sso my-organization

# Logout
github-cli auth logout

# Switch between multiple accounts
github-cli auth switch
```

## 📁 Repository Management

### Listing Repositories

```bash
# List your repositories
github-cli repo list

# List organization repositories
github-cli repo list --org my-organization

# List with specific sorting
github-cli repo list --sort updated --limit 20
```

### Viewing Repository Details

```bash
# View repository information
github-cli repo view owner/repository

# View with statistics
github-cli repo view owner/repository --stats

# View repository topics
github-cli repo topics owner/repository
```

### Creating Repositories

```bash
# Create a new repository
github-cli repo create --name my-project --description "My awesome project"

# Create private repository
github-cli repo create --name private-project --private

# Create with initialization
github-cli repo create --name new-project --auto-init --gitignore Python --license mit

# Create in organization
github-cli repo create --name team-project --org my-organization
```

### Repository Operations

```bash
# Update repository settings
github-cli repo update owner/repository --description "Updated description"

# Add topics to repository
github-cli repo topics owner/repository --topics "python,cli,github"

# Delete repository (use with caution!)
github-cli repo delete owner/repository
```

## 🔄 Pull Request Workflow

### Listing Pull Requests

```bash
# List open pull requests
github-cli pr list --repo owner/repository

# List all pull requests
github-cli pr list --repo owner/repository --state all

# List by author
github-cli pr list --repo owner/repository --author username
```

### Viewing Pull Request Details

```bash
# View pull request details
github-cli pr view --repo owner/repository --number 123

# View with diff
github-cli pr view --repo owner/repository --number 123 --diff

# View files changed
github-cli pr files --repo owner/repository --number 123
```

### Creating Pull Requests

```bash
# Create pull request
github-cli pr create --repo owner/repository \
  --title "Add new feature" \
  --head feature-branch \
  --base main \
  --body "This PR adds a new feature that..."

# Create draft pull request
github-cli pr create --repo owner/repository \
  --title "Work in progress" \
  --head wip-branch \
  --base main \
  --draft
```

### Pull Request Reviews

```bash
# Review pull request
github-cli pr review --repo owner/repository --number 123 --approve

# Request changes
github-cli pr review --repo owner/repository --number 123 \
  --request-changes --body "Please fix the following issues..."

# Add comment
github-cli pr review --repo owner/repository --number 123 \
  --comment --body "Looks good overall!"
```

### Merging Pull Requests

```bash
# Merge pull request
github-cli pr merge --repo owner/repository --number 123

# Squash and merge
github-cli pr merge --repo owner/repository --number 123 --squash

# Rebase and merge
github-cli pr merge --repo owner/repository --number 123 --rebase
```

## 🚀 GitHub Actions

### Listing Workflows

```bash
# List workflows in repository
github-cli actions list --repo owner/repository

# List workflow runs
github-cli actions runs --repo owner/repository

# List runs for specific workflow
github-cli actions runs --repo owner/repository --workflow ci.yml
```

### Viewing Workflow Details

```bash
# View workflow run details
github-cli actions view-run --repo owner/repository --id 123456

# View workflow run logs
github-cli actions logs --repo owner/repository --id 123456

# View specific job logs
github-cli actions logs --repo owner/repository --job-id 789012
```

### Managing Workflow Runs

```bash
# Cancel workflow run
github-cli actions cancel --repo owner/repository --id 123456

# Re-run workflow
github-cli actions rerun --repo owner/repository --id 123456

# Re-run failed jobs only
github-cli actions rerun --repo owner/repository --id 123456 --failed-only
```

## 🔍 Search Functionality

### Repository Search

```bash
# Search repositories
github-cli search repos "machine learning language:python"

# Search with filters
github-cli search repos "cli" --language python --stars ">100"

# Search user's repositories
github-cli search repos "user:octocat"
```

### Code Search

```bash
# Search code
github-cli search code "function authenticate" --language python

# Search in specific repository
github-cli search code "TODO" --repo owner/repository

# Search with file extension
github-cli search code "import requests" --extension py
```

### User and Issue Search

```bash
# Search users
github-cli search users "location:seattle"

# Search issues
github-cli search issues "is:open label:bug"

# Search pull requests
github-cli search prs "is:open author:username"
```

## 📱 Terminal User Interface (TUI)

### Launching the TUI

```bash
# Launch full TUI
github-cli tui

# Launch with specific theme
github-cli tui --theme light

# Launch in compact mode
github-cli tui --compact
```

### TUI Navigation

#### Keyboard Shortcuts

- **Tab/Shift+Tab**: Navigate between elements
- **Enter**: Select/activate item
- **Escape**: Go back/cancel
- **Ctrl+C**: Quit application
- **Ctrl+R**: Refresh data
- **Ctrl+L**: Toggle login/logout
- **F1**: Help
- **F5**: Refresh current view

#### Repository Management

- **Enter**: View repository details
- **C**: Create new repository
- **D**: Delete repository
- **F**: Fork repository
- **S**: Star/unstar repository

#### Pull Request Management

- **Enter**: View pull request details
- **C**: Create new pull request
- **M**: Merge pull request
- **R**: Review pull request

### TUI Features

#### Responsive Design
- Automatically adapts to terminal size
- Compact mode for small screens
- Sidebar toggles based on available space

#### Real-time Updates
- Background data refresh
- Live status indicators
- Automatic authentication handling

#### Accessibility
- Screen reader support
- High contrast mode
- Keyboard-only navigation

## ⚙️ Configuration

### Configuration File

GitHub CLI stores configuration in:
- **Linux/macOS**: `~/.config/github-cli/config.yaml`
- **Windows**: `%APPDATA%\github-cli\config.yaml`

### Configuration Options

```yaml
# Default configuration
api:
  base_url: "https://api.github.com"
  timeout: 30
  max_retries: 3

auth:
  default_scopes: "repo,user,gist"
  auto_refresh: true

tui:
  theme: "dark"
  auto_refresh: true
  refresh_interval: 30
  show_sidebar: true

output:
  format: "table"
  color: true
  pager: true
```

### Environment Variables

```bash
# GitHub token (alternative to OAuth)
export GITHUB_TOKEN="your_token_here"

# API base URL (for GitHub Enterprise)
export GITHUB_API_URL="https://github.company.com/api/v3"

# Debug mode
export GITHUB_CLI_DEBUG=1

# Custom config directory
export GITHUB_CLI_CONFIG_DIR="/path/to/config"
```

## 🎨 Customization

### Themes

```bash
# Available themes
github-cli config themes list

# Set theme
github-cli config set tui.theme dark

# Custom theme
github-cli config set tui.custom_theme /path/to/theme.yaml
```

### Output Formats

```bash
# Table format (default)
github-cli repo list --format table

# JSON format
github-cli repo list --format json

# YAML format
github-cli repo list --format yaml

# Custom template
github-cli repo list --format template --template "{{.name}}: {{.stars}}"
```

### Aliases

```bash
# Create alias
github-cli alias set repos "repo list"

# Use alias
github-cli repos

# List aliases
github-cli alias list

# Remove alias
github-cli alias remove repos
```

## 🚨 Troubleshooting

### Common Issues

#### Authentication Problems

```bash
# Clear authentication
github-cli auth logout

# Re-authenticate
github-cli auth login

# Check token status
github-cli auth status --verbose
```

#### Network Issues

```bash
# Test connectivity
github-cli api /user

# Use different API endpoint
github-cli config set api.base_url "https://api.github.com"

# Increase timeout
github-cli config set api.timeout 60
```

#### TUI Issues

```bash
# Reset TUI configuration
github-cli config reset tui

# Run in debug mode
GITHUB_CLI_DEBUG=1 github-cli tui

# Check terminal compatibility
github-cli tui --check-compatibility
```

### Getting Help

```bash
# General help
github-cli --help

# Command-specific help
github-cli repo --help
github-cli pr create --help

# Show version and debug info
github-cli --version --verbose

# Check configuration
github-cli config list
```

### Log Files

Logs are stored in:
- **Linux/macOS**: `~/.config/github-cli/logs/`
- **Windows**: `%APPDATA%\github-cli\logs\`

```bash
# View recent logs
tail -f ~/.config/github-cli/logs/github_cli.log

# View authentication logs
tail -f ~/.config/github-cli/logs/auth.log
```

## 📚 Advanced Usage

### Scripting and Automation

```bash
# Use in scripts
#!/bin/bash
repos=$(github-cli repo list --format json)
echo "$repos" | jq '.[] | select(.language == "Python") | .name'

# Batch operations
github-cli repo list --format json | \
  jq -r '.[] | select(.stargazers_count > 100) | .full_name' | \
  xargs -I {} github-cli repo view {}
```

### Integration with Git

```bash
# Create repository and push
git init my-project
cd my-project
echo "# My Project" > README.md
git add README.md
git commit -m "Initial commit"

github-cli repo create --name my-project --auto-init=false
git remote add origin $(github-cli repo view my-project --format json | jq -r '.clone_url')
git push -u origin main
```

### Workflow Automation

```bash
# Automated PR workflow
github-cli pr create --repo owner/repo --title "Auto PR" --head feature --base main
PR_NUMBER=$(github-cli pr list --repo owner/repo --head feature --format json | jq -r '.[0].number')
github-cli pr review --repo owner/repo --number $PR_NUMBER --approve
github-cli pr merge --repo owner/repo --number $PR_NUMBER --squash
```

## 🔗 Additional Resources

- [Installation Guide](installation.md)
- [Command Reference](commands.md)
- [TUI Guide](tui-guide.md)
- [API Documentation](../api/README.md)
- [Troubleshooting Guide](troubleshooting.md)
