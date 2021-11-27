from dataclasses import dataclass
from typing import List, Tuple

import requests

OPENCITATIONS_API = 'https://opencitations.net/index/api/v1/metadata/'
REFERENCES_SPLIT = '; '
CITATIONS_SPLIT = '; '

@dataclass
class CrossReferences:
    doi: str

    def get_citations_references(self) -> Tuple[List[str], List[str]]:
        """
        Get citations & references from opencitation api based on the doi.

        Returns:
            Tuple[List[str], List[str]]: Tuple of citations & references.
        """
        oc_output = requests.get(url=OPENCITATIONS_API + self.doi).json()
        citation = [oc["citation"] for oc in oc_output]
        refs = [oc["reference"] for oc in oc_output]
        final_citation = citation[0].split(CITATIONS_SPLIT)
        final_references = refs[0].split(REFERENCES_SPLIT)
        return final_citation, final_references
