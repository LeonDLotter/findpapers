from dataclasses import dataclass

import requests

OPENCITATIONS_API = 'https://opencitations.net/index/api/v1/metadata/'
REFERENCES_SPLIT = '; '

@dataclass
class References:
    search_results: dict

    def get_references(self) -> dict:
        """
        Get references from opencitation api based on the doi and
        add it to search response from findpapers.

        Returns:
            dict: Original response with references key added to it.
        """
        for paper in self.search_results['papers']:
            doi = paper['doi']
            req = requests.get(url=OPENCITATIONS_API + doi)
            citations = req.json()
            refs = [
                citation['reference'] for citation in citations
            ]
            if refs[0] != '':
                paper['reference'] = [ref.split(REFERENCES_SPLIT) for ref in refs]
            else:
                paper['reference'] = refs
        
        return self.search_results