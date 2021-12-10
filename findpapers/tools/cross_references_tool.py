import requests

from typing import List, Tuple

OPENCITATIONS_API = 'https://opencitations.net/index/api/v1/metadata/'
REFERENCES_SPLIT = '; '
CITATIONS_SPLIT = '; '


def get_cross_references(doi: str = '') -> Tuple[List[str], List[str]]:
    """Get citations & references from opencitation api based on the doi.

    Args:
        doi (str, optional): [description]. Defaults to ''.

    Returns:
        Tuple[List[str], List[str]]: Tuple of citations & references
    """
    citations = []
    references = []

    if doi is not None:
        # return first found paper with the corresponding doi
        oc_output = requests.get(url=OPENCITATIONS_API + doi).json()[0]
        if len(oc_output['citation']) > 0:
            citations = oc_output['citation'].replace(' ', '').split(';')
        if len(oc_output['reference']) > 0:
            references = oc_output['reference'].replace(' ', '').split(';')

    return citations, references
