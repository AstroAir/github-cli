# GitHub CLI Documentation

Welcome to the comprehensive documentation for GitHub CLI - an advanced terminal-based GitHub client with rich user interface capabilities.

## 📚 Documentation Structure

### User Documentation
- **[User Guide](user/README.md)** - Complete user manual with examples and tutorials
- **[Installation Guide](user/installation.md)** - Step-by-step installation instructions
- **[Command Reference](user/commands.md)** - Complete command-line reference
- **[TUI Guide](user/tui-guide.md)** - Terminal User Interface usage guide

### Developer Documentation
- **[Developer Guide](developer/README.md)** - Complete development setup and guidelines
- **[Architecture Overview](developer/architecture.md)** - System architecture and design patterns
- **[Contributing Guide](developer/contributing.md)** - How to contribute to the project
- **[Testing Guide](developer/testing.md)** - Testing strategies and guidelines

### API Documentation
- **[API Overview](api/README.md)** - GitHub API client architecture
- **[Client](api/client.md)** - Core API client documentation
- **[Repositories](api/repositories.md)** - Repository management API
- **[Pull Requests](api/pull-requests.md)** - Pull request operations API
- **[Actions](api/actions.md)** - GitHub Actions workflow API
- **[Issues](api/issues.md)** - Issue management API
- **[Search](api/search.md)** - Search functionality API

### Authentication System
- **[Authentication Overview](auth/README.md)** - Authentication system architecture
- **[OAuth Flow](auth/oauth.md)** - OAuth device flow implementation
- **[Token Management](auth/tokens.md)** - Token storage and lifecycle
- **[SSO Support](auth/sso.md)** - Single Sign-On integration

### Terminal User Interface (TUI)
- **[TUI Overview](tui/README.md)** - TUI system architecture
- **[Responsive Design](tui/responsive.md)** - Adaptive layout system
- **[Widgets](tui/widgets.md)** - Custom widget components
- **[Styling](tui/styling.md)** - CSS styling and themes

### Data Models
- **[Models Overview](models/README.md)** - Data model architecture
- **[Repository Model](models/repository.md)** - Repository data structures
- **[User Model](models/user.md)** - User and organization models
- **[Workflow Model](models/workflow.md)** - GitHub Actions workflow models

### Utilities
- **[Utilities Overview](utils/README.md)** - Utility modules documentation
- **[Configuration](utils/config.md)** - Configuration management
- **[Error Handling](utils/exceptions.md)** - Exception handling system
- **[Performance](utils/performance.md)** - Performance optimization tools

## 🚀 Quick Start

1. **Installation**: See [Installation Guide](user/installation.md)
2. **Authentication**: Follow [OAuth Setup](auth/oauth.md)
3. **Basic Usage**: Check [User Guide](user/README.md)
4. **TUI Interface**: Launch with `github-cli tui`

## 🏗️ Architecture Overview

GitHub CLI is built with a modular architecture:

```
github_cli/
├── api/           # GitHub API client modules
├── auth/          # Authentication and authorization
├── tui/           # Terminal User Interface (Textual-based)
├── ui/            # Legacy Rich-based UI components
├── models/        # Data models and structures
├── utils/         # Utility functions and helpers
└── git/           # Git integration utilities
```

## 🔧 Key Features

- **🔐 Secure Authentication** - OAuth device flow with token management
- **📊 Interactive TUI** - Modern terminal interface with responsive design
- **🚀 GitHub Actions** - Complete workflow management
- **📁 Repository Management** - Full repository lifecycle operations
- **🔄 Pull Request Workflow** - Create, review, and merge pull requests
- **📋 Rich Terminal Output** - Beautiful tables, colors, and formatting

## 📖 Getting Help

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Browse this comprehensive documentation
- **CLI Help**: Use `github-cli --help` for command-line help

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](developer/contributing.md) for details on:

- Setting up the development environment
- Code style and standards
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
