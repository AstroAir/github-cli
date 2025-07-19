# Repository API

The `RepositoryAPI` provides comprehensive repository management functionality including creation, updates, statistics, and metadata operations.

## 🏗️ Class Overview

```python
class RepositoryAPI:
    """API for working with GitHub repositories"""
    
    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui
```

## 📚 Core Methods

### Repository Listing

#### List User Repositories
```python
async def list_user_repos(
    self, 
    username: Optional[str] = None,
    sort: str = "updated",
    per_page: int = 30,
    page: int = 1
) -> List[Repository]
```

**Parameters:**
- `username`: Target user (None for authenticated user)
- `sort`: Sort order (`updated`, `created`, `pushed`, `full_name`)
- `per_page`: Results per page (1-100)
- `page`: Page number

**Example:**
```python
repo_api = RepositoryAPI(client)

# List your repositories
my_repos = await repo_api.list_user_repos()

# List another user's repositories
user_repos = await repo_api.list_user_repos("octocat")

# With custom sorting
recent_repos = await repo_api.list_user_repos(
    sort="updated",
    per_page=50
)
```

#### List Organization Repositories
```python
async def list_org_repos(
    self,
    org: str,
    type: str = "all",
    sort: str = "updated",
    per_page: int = 30
) -> List[Repository]
```

**Parameters:**
- `org`: Organization name
- `type`: Repository type (`all`, `public`, `private`, `forks`, `sources`, `member`)
- `sort`: Sort order
- `per_page`: Results per page

**Example:**
```python
# List organization repositories
org_repos = await repo_api.list_org_repos("github")

# Only public repositories
public_repos = await repo_api.list_org_repos("github", type="public")
```

### Repository Details

#### Get Repository
```python
async def get_repo(self, repo_name: str) -> Repository
```

**Parameters:**
- `repo_name`: Repository in format "owner/repo"

**Example:**
```python
# Get repository details
repo = await repo_api.get_repo("octocat/Hello-World")
print(f"Repository: {repo.full_name}")
print(f"Description: {repo.description}")
print(f"Stars: {repo.stargazers_count}")
```

### Repository Creation

#### Create Repository
```python
async def create_repo(
    self,
    name: str,
    description: Optional[str] = None,
    private: bool = False,
    org: Optional[str] = None,
    **kwargs
) -> Repository
```

**Parameters:**
- `name`: Repository name
- `description`: Repository description
- `private`: Whether repository is private
- `org`: Organization name (for org repositories)
- `**kwargs`: Additional repository settings

**Additional Options:**
- `auto_init`: Initialize with README
- `gitignore_template`: Gitignore template name
- `license_template`: License template name
- `homepage`: Repository homepage URL
- `has_issues`: Enable issues
- `has_projects`: Enable projects
- `has_wiki`: Enable wiki

**Example:**
```python
# Create personal repository
repo = await repo_api.create_repo(
    name="my-project",
    description="My awesome project",
    private=False,
    auto_init=True,
    gitignore_template="Python",
    license_template="mit"
)

# Create organization repository
org_repo = await repo_api.create_repo(
    name="team-project",
    description="Team collaboration project",
    org="my-org",
    private=True,
    has_issues=True,
    has_projects=True
)
```

### Repository Updates

#### Update Repository
```python
async def update_repo(self, repo_name: str, **kwargs) -> Repository
```

**Parameters:**
- `repo_name`: Repository in format "owner/repo"
- `**kwargs`: Fields to update

**Updatable Fields:**
- `name`: Repository name
- `description`: Description
- `homepage`: Homepage URL
- `private`: Visibility
- `has_issues`: Enable/disable issues
- `has_projects`: Enable/disable projects
- `has_wiki`: Enable/disable wiki
- `default_branch`: Default branch name

**Example:**
```python
# Update repository settings
updated_repo = await repo_api.update_repo(
    "owner/repo",
    description="Updated description",
    homepage="https://example.com",
    has_issues=True
)
```

#### Delete Repository
```python
async def delete_repo(self, repo_name: str) -> bool
```

**Example:**
```python
# Delete repository (use with caution!)
success = await repo_api.delete_repo("owner/repo")
if success:
    print("Repository deleted successfully")
```

### Repository Topics

#### Get Topics
```python
async def get_repo_topics(self, repo_name: str) -> List[str]
```

#### Set Topics
```python
async def set_repo_topics(self, repo_name: str, topics: List[str]) -> List[str]
```

**Example:**
```python
# Get current topics
topics = await repo_api.get_repo_topics("owner/repo")
print(f"Current topics: {topics}")

# Set new topics
new_topics = ["python", "cli", "github", "api"]
updated_topics = await repo_api.set_repo_topics("owner/repo", new_topics)
```

### Repository Statistics

#### Get Repository Statistics
```python
async def get_repo_stats(self, repo_name: str) -> Dict[str, Any]
```

**Returns comprehensive statistics including:**
- Contributor statistics
- Commit activity
- Code frequency
- Participation data
- Language breakdown

**Example:**
```python
# Get detailed repository statistics
stats = await repo_api.get_repo_stats("owner/repo")

print(f"Contributors: {len(stats['contributors'])}")
print(f"Total commits: {stats['commit_activity']['total']}")
print(f"Languages: {list(stats['languages'].keys())}")

# Access specific statistics
contributors = stats['contributors']
for contributor in contributors[:5]:  # Top 5 contributors
    print(f"{contributor['author']['login']}: {contributor['total']} commits")
```

### Repository Content

#### Get Repository Contents
```python
async def get_repo_contents(
    self,
    repo_name: str,
    path: str = "",
    ref: Optional[str] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `repo_name`: Repository in format "owner/repo"
- `path`: Path within repository
- `ref`: Git reference (branch, tag, commit)

**Example:**
```python
# Get root directory contents
contents = await repo_api.get_repo_contents("owner/repo")

# Get specific directory
src_contents = await repo_api.get_repo_contents("owner/repo", "src")

# Get contents from specific branch
dev_contents = await repo_api.get_repo_contents("owner/repo", "", "develop")
```

## 🎯 CLI Command Handler

The module includes a command handler for CLI integration:

```python
async def handle_repo_command(
    args: Dict[str, Any], 
    client: GitHubClient, 
    ui: TerminalUI
) -> None
```

### Supported Commands

#### List Repositories
```bash
github-cli repo list [--org ORGANIZATION]
```

#### View Repository
```bash
github-cli repo view OWNER/REPO
```

#### Create Repository
```bash
github-cli repo create --name NAME [OPTIONS]
```

**Options:**
- `--description`: Repository description
- `--private`: Make repository private
- `--org`: Create in organization
- `--auto-init`: Initialize with README
- `--gitignore`: Gitignore template
- `--license`: License template

#### Update Repository
```bash
github-cli repo update OWNER/REPO [OPTIONS]
```

#### Delete Repository
```bash
github-cli repo delete OWNER/REPO
```

#### Manage Topics
```bash
github-cli repo topics OWNER/REPO --topics "topic1,topic2,topic3"
```

## 📊 Repository Model

The API returns `Repository` objects with the following key attributes:

```python
@dataclass
class Repository:
    id: int
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    html_url: str
    clone_url: str
    ssh_url: str
    homepage: Optional[str]
    language: Optional[str]
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    default_branch: str
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    size: int
    has_issues: bool
    has_projects: bool
    has_wiki: bool
    archived: bool
    disabled: bool
    visibility: str
    topics: List[str]
    license: Optional[Dict[str, Any]]
    owner: Dict[str, Any]
```

## 🚨 Error Handling

Common errors and their handling:

```python
try:
    repo = await repo_api.get_repo("owner/repo")
except NotFoundError:
    print("Repository not found")
except ForbiddenError:
    print("Access denied - repository may be private")
except GitHubCLIError as e:
    print(f"API error: {e}")
```

## 📝 Usage Examples

### Complete Repository Workflow
```python
async def repository_workflow():
    repo_api = RepositoryAPI(client)
    
    # Create repository
    repo = await repo_api.create_repo(
        name="my-project",
        description="My awesome project",
        auto_init=True,
        gitignore_template="Python",
        license_template="mit"
    )
    
    # Set topics
    await repo_api.set_repo_topics(repo.full_name, [
        "python", "cli", "github"
    ])
    
    # Update settings
    await repo_api.update_repo(repo.full_name,
        homepage="https://example.com",
        has_wiki=True
    )
    
    # Get statistics
    stats = await repo_api.get_repo_stats(repo.full_name)
    print(f"Repository created with {stats['languages']} languages")
    
    return repo
```

### Repository Discovery
```python
async def discover_repositories():
    repo_api = RepositoryAPI(client)
    
    # Find popular Python repositories
    my_repos = await repo_api.list_user_repos()
    python_repos = [r for r in my_repos if r.language == "Python"]
    
    # Sort by stars
    popular_repos = sorted(python_repos, 
                          key=lambda r: r.stargazers_count, 
                          reverse=True)
    
    for repo in popular_repos[:5]:
        print(f"{repo.full_name}: {repo.stargazers_count} stars")
        
        # Get detailed stats
        stats = await repo_api.get_repo_stats(repo.full_name)
        print(f"  Contributors: {len(stats['contributors'])}")
        print(f"  Languages: {list(stats['languages'].keys())}")
```

## 🔗 Related Documentation

- [GitHub Repository API](https://docs.github.com/en/rest/repos/repos)
- [Repository Model](../models/repository.md)
- [API Client](client.md)
- [Error Handling](../utils/exceptions.md)
