# Data Models

The GitHub CLI data models provide structured representations of GitHub entities with type safety, validation, and convenient methods for data manipulation.

## 🏗️ Architecture Overview

The models system is built with modern Python features:

```
github_cli/models/
├── __init__.py          # Model exports and utilities
├── repository.py        # Repository data structures
├── user.py             # User and organization models
├── issue.py            # Issue management models
├── pull_request.py     # Pull request models
├── workflow.py         # GitHub Actions workflow models
├── notification.py     # Notification models
├── release.py          # Release and asset models
└── team.py             # Team and organization models
```

## 🔧 Core Design Principles

### Type Safety

All models use Python's type system for safety and IDE support:

```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Repository:
    """GitHub repository model with full type annotations."""
    id: int
    name: str
    full_name: str
    private: bool
    description: Optional[str]
    topics: List[str]
    owner: Dict[str, Any]
```

### Validation

Models use Pydantic for runtime validation:

```python
from pydantic import BaseModel, Field, validator

class User(BaseModel):
    """User model with validation."""
    login: str = Field(min_length=1, max_length=39)
    id: int = Field(gt=0)
    email: Optional[str] = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
    
    @validator('login')
    def validate_login(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Invalid username format')
        return v
```

### Immutability

Core models are immutable for thread safety:

```python
@dataclass(frozen=True, slots=True)
class AuthTokenResponse:
    """Immutable authentication token response."""
    access_token: str
    token_type: str
    scope: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
```

## 📊 Core Models

### Repository Model

Represents GitHub repositories with comprehensive metadata:

```python
@dataclass
class Repository:
    """GitHub repository model"""
    
    # Basic information
    id: int
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    fork: bool
    
    # URLs and references
    html_url: str
    clone_url: str
    ssh_url: str
    homepage: Optional[str]
    
    # Statistics
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    size: int
    
    # Metadata
    language: Optional[str]
    topics: List[str]
    license: Optional[Dict[str, Any]]
    default_branch: str
    visibility: str
    
    # Timestamps
    created_at: str
    updated_at: str
    pushed_at: str
    
    # Status flags
    archived: bool = False
    disabled: bool = False
    
    # Owner information
    owner: Dict[str, Any]
```

**Key Methods:**

```python
@classmethod
def from_json(cls, data: Dict[str, Any]) -> 'Repository':
    """Create Repository from GitHub API response."""
    return cls(
        id=data["id"],
        name=data["name"],
        full_name=data["full_name"],
        # ... map all fields
    )

@property
def created_date(self) -> datetime:
    """Get creation date as datetime object."""
    return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

@property
def is_public(self) -> bool:
    """Check if repository is public."""
    return not self.private

@property
def owner_login(self) -> str:
    """Get owner's login name."""
    return self.owner.get("login", "")
```

### User Model

Represents GitHub users and organizations:

```python
@dataclass
class User:
    """GitHub User model"""
    
    # Core identity
    id: int
    login: str
    node_id: str
    type: str  # "User" or "Organization"
    site_admin: bool
    
    # Profile information
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    blog: Optional[str] = None
    twitter_username: Optional[str] = None
    
    # URLs
    avatar_url: str
    html_url: str
    url: str
    
    # Statistics
    public_repos: int = 0
    public_gists: int = 0
    followers: int = 0
    following: int = 0
    
    # Private information (for authenticated user)
    private_gists: int = 0
    total_private_repos: int = 0
    owned_private_repos: int = 0
    disk_usage: int = 0
    collaborators: int = 0
    two_factor_authentication: bool = False
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Plan information
    plan: Dict[str, Any] = field(default_factory=dict)
```

### Issue Model

Represents GitHub issues with full metadata:

```python
@dataclass
class Issue:
    """GitHub issue model"""
    
    # Core information
    id: int
    number: int
    title: str
    body: Optional[str]
    state: str  # "open" or "closed"
    
    # Assignment and collaboration
    user: Dict[str, Any]  # Issue creator
    assignee: Optional[Dict[str, Any]]
    assignees: List[Dict[str, Any]]
    
    # Organization
    labels: List[Dict[str, Any]]
    milestone: Optional[Dict[str, Any]]
    
    # Metadata
    comments: int
    locked: bool
    author_association: str
    
    # URLs
    html_url: str
    url: str
    repository_url: str
    
    # Timestamps
    created_at: str
    updated_at: str
    closed_at: Optional[str]
```

**Computed Properties:**

```python
@property
def created_date(self) -> datetime:
    """Get creation date as datetime."""
    return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

@property
def is_open(self) -> bool:
    """Check if issue is open."""
    return self.state == "open"

@property
def creator_name(self) -> str:
    """Get creator's login name."""
    return self.user.get("login", "")

@property
def label_names(self) -> List[str]:
    """Get list of label names."""
    return [label.get("name", "") for label in self.labels]
```

### Pull Request Model

Extends Issue model with PR-specific features:

```python
@dataclass
class PullRequest(Issue):
    """GitHub pull request model"""
    
    # Branch information
    head: Dict[str, Any]  # Source branch
    base: Dict[str, Any]  # Target branch
    
    # Merge information
    merged: bool
    mergeable: Optional[bool]
    mergeable_state: Optional[str]
    merged_by: Optional[Dict[str, Any]]
    merged_at: Optional[str]
    
    # PR-specific metadata
    draft: bool
    requested_reviewers: List[Dict[str, Any]]
    requested_teams: List[Dict[str, Any]]
    
    # Change statistics
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits: int = 0
    review_comments: int = 0
```

**Additional Properties:**

```python
@property
def head_ref(self) -> str:
    """Get source branch name."""
    return self.head.get("ref", "")

@property
def base_ref(self) -> str:
    """Get target branch name."""
    return self.base.get("ref", "")

@property
def is_merged(self) -> bool:
    """Check if PR is merged."""
    return self.merged

@property
def change_summary(self) -> str:
    """Get formatted change summary."""
    return f"+{self.additions} -{self.deletions} files: {self.changed_files}"
```

### Workflow Models

GitHub Actions workflow representations:

```python
@dataclass
class Workflow:
    """GitHub Actions workflow model"""
    
    id: int
    name: str
    path: str
    state: str  # "active" or "disabled"
    created_at: datetime
    updated_at: datetime
    url: str
    html_url: str
    badge_url: str

@dataclass
class WorkflowRun:
    """GitHub Actions workflow run model"""
    
    id: int
    name: Optional[str]
    workflow_id: int
    run_number: int
    status: str  # "queued", "in_progress", "completed"
    conclusion: Optional[str]  # "success", "failure", "cancelled"
    head_branch: str
    head_sha: str
    event: str
    created_date: datetime
    updated_date: datetime
    html_url: str

@dataclass
class WorkflowJob:
    """GitHub Actions workflow job model"""
    
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    started_date: Optional[datetime]
    completed_date: Optional[datetime]
    runner_name: Optional[str]
    steps: List[Dict[str, Any]]
    html_url: str
```

## 🔄 Model Utilities

### Factory Methods

Consistent creation from API responses:

```python
class ModelFactory:
    """Factory for creating models from API responses."""
    
    @staticmethod
    def create_repository(data: Dict[str, Any]) -> Repository:
        """Create Repository from API data."""
        return Repository.from_json(data)
    
    @staticmethod
    def create_user(data: Dict[str, Any]) -> User:
        """Create User from API data."""
        return User.from_json(data)
    
    @staticmethod
    def create_issue(data: Dict[str, Any]) -> Issue:
        """Create Issue from API data."""
        return Issue.from_json(data)
```

### Serialization

Convert models to various formats:

```python
class ModelSerializer:
    """Serialization utilities for models."""
    
    @staticmethod
    def to_dict(model: Any) -> Dict[str, Any]:
        """Convert model to dictionary."""
        if hasattr(model, '__dict__'):
            return asdict(model)
        return model.dict() if hasattr(model, 'dict') else {}
    
    @staticmethod
    def to_json(model: Any) -> str:
        """Convert model to JSON string."""
        return json.dumps(ModelSerializer.to_dict(model), default=str)
    
    @staticmethod
    def from_json(json_str: str, model_class: type) -> Any:
        """Create model from JSON string."""
        data = json.loads(json_str)
        return model_class.from_json(data)
```

### Validation

Runtime validation and type checking:

```python
class ModelValidator:
    """Validation utilities for models."""
    
    @staticmethod
    def validate_repository(repo: Repository) -> List[str]:
        """Validate repository model."""
        errors = []
        
        if not repo.name:
            errors.append("Repository name is required")
        
        if repo.stargazers_count < 0:
            errors.append("Star count cannot be negative")
        
        return errors
    
    @staticmethod
    def validate_user(user: User) -> List[str]:
        """Validate user model."""
        errors = []
        
        if not user.login:
            errors.append("User login is required")
        
        if user.id <= 0:
            errors.append("User ID must be positive")
        
        return errors
```

## 📝 Usage Examples

### Creating Models from API Data

```python
# Create repository from API response
api_data = await client.get("/repos/owner/repo")
repository = Repository.from_json(api_data.data)

print(f"Repository: {repository.full_name}")
print(f"Stars: {repository.stargazers_count}")
print(f"Language: {repository.language}")
print(f"Created: {repository.created_date}")
```

### Working with Collections

```python
# Process multiple repositories
repos_data = await client.get("/user/repos")
repositories = [Repository.from_json(repo) for repo in repos_data.data]

# Filter and sort
python_repos = [r for r in repositories if r.language == "Python"]
popular_repos = sorted(repositories, key=lambda r: r.stargazers_count, reverse=True)

# Display information
for repo in popular_repos[:5]:
    print(f"{repo.full_name}: {repo.stargazers_count} stars")
```

### Model Validation

```python
# Validate model data
repository = Repository.from_json(api_data)
errors = ModelValidator.validate_repository(repository)

if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Repository data is valid")
```

### Serialization

```python
# Convert to dictionary
repo_dict = ModelSerializer.to_dict(repository)

# Convert to JSON
repo_json = ModelSerializer.to_json(repository)

# Save to file
with open("repository.json", "w") as f:
    f.write(repo_json)

# Load from file
with open("repository.json", "r") as f:
    loaded_repo = ModelSerializer.from_json(f.read(), Repository)
```

## 🧪 Testing

### Model Testing

```python
import pytest
from github_cli.models.repository import Repository

def test_repository_creation():
    """Test repository model creation."""
    repo_data = {
        "id": 123,
        "name": "test-repo",
        "full_name": "owner/test-repo",
        "private": False,
        "description": "Test repository",
        # ... other required fields
    }
    
    repo = Repository.from_json(repo_data)
    
    assert repo.id == 123
    assert repo.name == "test-repo"
    assert repo.is_public is True

def test_repository_properties():
    """Test repository computed properties."""
    repo = Repository(
        created_at="2023-01-01T00:00:00Z",
        # ... other fields
    )
    
    assert isinstance(repo.created_date, datetime)
    assert repo.created_date.year == 2023
```

## 🔗 Related Documentation

- [Repository Model](repository.md) - Detailed repository model documentation
- [User Model](user.md) - User and organization models
- [Workflow Model](workflow.md) - GitHub Actions models
- [API Integration](../api/README.md) - API client integration
- [Validation Guide](validation.md) - Model validation patterns
