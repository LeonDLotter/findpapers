from typing import List

import requests

OPENCITATIONS_API = 'https://opencitations.net/index/api/v1/metadata/'
REFERENCES_SPLIT = '; '

class References:
    def __init__(self, doi: str) -> None:
        self.doi = doi

    def get_references(self) -> List[List[str]]:
        """
        Get references from opencitation api based on the doi.

        Returns:
            List[List[str]]: List of the references.
        """
        self.req = requests.get(
            url=OPENCITATIONS_API + self.doi,
        )
        self.citations = self.req.json()
        self.refs = [
            self.citation["reference"] for self.citation in self.citations
        ]
        return [self.ref.split(REFERENCES_SPLIT) for self.ref in self.refs]
