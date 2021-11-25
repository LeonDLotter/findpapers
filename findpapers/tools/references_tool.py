from dataclasses import dataclass
from typing import List

import requests

OPENCITATIONS_API = 'https://opencitations.net/index/api/v1/metadata/'
REFERENCES_SPLIT = '; '

@dataclass
class References:
    doi: str

    def get_references(self) -> List[str]:
        """
        Get references from opencitation api based on the doi.

        Returns:
            List[str]: dois of references cited by input doi.
        """
        req = requests.get(url=OPENCITATIONS_API + self.doi)
        citations = req.json()
        refs = [citation["reference"] for citation in citations]
        return refs[0].split(REFERENCES_SPLIT)
