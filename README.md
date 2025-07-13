# GitHub CLI

An advanced terminal-based GitHub client with a rich user interface. This command-line tool provides intuitive access to GitHub features like repositories, pull requests, issues, and GitHub Actions directly from your terminal.

## Features

- 🔐 Secure authentication via OAuth device flow
- 📊 Interactive dashboard with GitHub activity overview
- 📁 Repository management (create, view, list, delete)
- 🔄 Pull request operations (create, review, merge, diff)
- 🚀 GitHub Actions workflow management
- 📋 Rich terminal UI with tables, colors, and panels

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/github-cli.git
cd github-cli

# Install the package
pip install -e .
```

## Usage

### Authentication

First, authenticate with your GitHub account:

```bash
# Start OAuth device flow
github-cli auth login

# Check authentication status
github-cli auth status
```

### Repositories

```bash
# List your repositories
github-cli repo list

# View repository details
github-cli repo view owner/repo

# Create a new repository
github-cli repo create --name myrepo --description "My new repository"

# Add topics to a repository
github-cli repo topics --name owner/repo --topics "topic1,topic2"
```

### Pull Requests

```bash
# List pull requests in a repository
github-cli pr list --repo owner/repo

# View a specific pull request
github-cli pr view --repo owner/repo --number 123

# Create a pull request
github-cli pr create --repo owner/repo --title "Fix bug" --head feature-branch --base main

# Merge a pull request
github-cli pr merge --repo owner/repo --number 123
```

### GitHub Actions

```bash
# List workflows in a repository
github-cli actions list --repo owner/repo

# View workflow runs
github-cli actions runs --repo owner/repo

# View a specific workflow run
github-cli actions view-run --repo owner/repo --id 123456

# Re-run a workflow
github-cli actions rerun --repo owner/repo --id 123456
```

### Dashboard

Launch an interactive dashboard with all your GitHub activity:

```bash
github-cli dashboard
```

## Development

### Requirements

- Python 3.8+
- aiohttp
- rich
- questionary
- keyring

### Project Structure

```text
github_cli/
├── __init__.py         # Package initialization
├── __main__.py         # Command-line entry point
├── api/                # GitHub API interfaces
│   ├── actions.py      # GitHub Actions API
│   ├── client.py       # Core API client
│   ├── pull_requests.py # Pull requests API
│   └── repositories.py # Repository API
├── auth/               # Authentication
│   └── authenticator.py # OAuth authentication
├── models/             # Data models
│   ├── repository.py   # Repository model
│   └── ...
├── ui/                 # User interface
│   ├── dashboard.py    # Interactive dashboard
│   └── terminal.py     # Terminal UI components
└── utils/              # Utilities
    ├── config.py       # Configuration management
    └── exceptions.py   # Custom exceptions
```

## License

MIT License
