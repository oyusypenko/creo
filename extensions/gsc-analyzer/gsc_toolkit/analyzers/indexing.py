"""Google Indexing API for requesting URL indexing."""

import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

import requests
from google.oauth2 import service_account

from ..core.config import KEY_FILE
from ..core.utils import print_error, print_success


class IndexingAPI:
    """Google Indexing API for requesting URL indexing."""

    INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    BATCH_ENDPOINT = "https://indexing.googleapis.com/batch"

    def __init__(self, key_file: str = KEY_FILE):
        self.key_file = key_file
        self._credentials = None
        self._session = None

    def _get_credentials(self):
        """Get service account credentials with indexing scope."""
        if not self._credentials:
            if not Path(self.key_file).exists():
                print_error(f"Key file not found: {self.key_file}")
                return None

            self._credentials = service_account.Credentials.from_service_account_file(
                self.key_file,
                scopes=['https://www.googleapis.com/auth/indexing']
            )
        return self._credentials

    def _get_session(self):
        """Get authenticated requests session."""
        if not self._session:
            from google.auth.transport.requests import AuthorizedSession
            credentials = self._get_credentials()
            if credentials:
                self._session = AuthorizedSession(credentials)
        return self._session

    def request_indexing(self, url: str, action: str = "URL_UPDATED") -> Dict:
        """
        Request indexing for a URL.

        Args:
            url: URL to index
            action: "URL_UPDATED" or "URL_DELETED"

        Returns:
            API response dict
        """
        session = self._get_session()
        if not session:
            return {"error": "Failed to get authenticated session"}

        body = {
            "url": url,
            "type": action
        }

        try:
            response = session.post(self.INDEXING_ENDPOINT, json=body)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "url": url}

    def request_batch_indexing(
        self,
        urls: List[str],
        action: str = "URL_UPDATED",
        delay: float = 0.5
    ) -> List[Dict]:
        """
        Request indexing for multiple URLs.

        Note: Daily quota is 200 requests per property.
        """
        results = []

        for i, url in enumerate(urls):
            print(f"[{i+1}/{len(urls)}] Requesting indexing: {url[:50]}...")
            result = self.request_indexing(url, action)
            results.append(result)

            if "error" in result:
                print_error(f"  Error: {result['error']}")
            else:
                notify_time = result.get('urlNotificationMetadata', {}).get('latestUpdate', {}).get('notifyTime', 'OK')
                print_success(f"  Indexed: {notify_time}")

            if i < len(urls) - 1:
                time.sleep(delay)

        return results

    def get_urls_from_sitemap(self, sitemap_url: str) -> List[str]:
        """Fetch URLs from a sitemap."""
        try:
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            # Handle namespace
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            urls = []
            for url_elem in root.findall('.//sm:url/sm:loc', ns):
                if url_elem.text:
                    urls.append(url_elem.text.strip())

            # Also check for sitemap index
            for sitemap_elem in root.findall('.//sm:sitemap/sm:loc', ns):
                if sitemap_elem.text:
                    # Recursively get URLs from nested sitemaps
                    nested_urls = self.get_urls_from_sitemap(sitemap_elem.text.strip())
                    urls.extend(nested_urls)

            return urls

        except Exception as e:
            print_error(f"Error fetching sitemap: {e}")
            return []
