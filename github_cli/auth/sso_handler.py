"""
SSO handler for GitHub authentication
"""

from typing import Dict, Any
import time
import webbrowser
import aiohttp

from github_cli.utils.config import Config


class SSOHandler:
    """Handler for GitHub SSO authentication"""

    def __init__(self, config: Config):
        """Initialize the SSO handler"""
        self.config = config
        self.sso_pending: dict[str, Any] = {}

    async def handle_sso_challenge(self, response_headers: Dict[str, str], token: str) -> None:
        """Handle an SSO authorization challenge"""
        if 'x-github-sso' not in response_headers:
            return

        # Extract the SSO URL from the header
        sso_header = response_headers['x-github-sso']
        if 'url=' not in sso_header:
            return

        sso_url = sso_header.split('url=')[1].split(';')[0]

        print("\nThis organization requires SSO authorization.")
        print(f"Opening browser to authorize: {sso_url}")

        # Open the SSO URL in the browser
        webbrowser.open(sso_url)

        # Mark this token as pending SSO authorization
        self.sso_pending[token] = {
            'url': sso_url,
            'timestamp': time.time()
        }

        print("Complete the authorization in your browser, then continue...")

    async def verify_sso(self, token: str, org: str) -> bool:
        """Verify if SSO authorization has been completed"""
        # Simple API call to check authorization
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.github.com/orgs/{org}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        # SSO verification successful
                        if token in self.sso_pending:
                            del self.sso_pending[token]
                        return True
                    elif 'x-github-sso' in response.headers:
                        # Still needs SSO authorization
                        return False
                    else:
                        # Other issue
                        return False
        except Exception:
            return False

    async def configure(self, org: str) -> None:
        """Configure SSO for an organization"""
        print(f"🔧 Configuring SSO for organization: {org}")
        print("This feature is planned for a future release.")
        # TODO: Implement SSO configuration
        pass
