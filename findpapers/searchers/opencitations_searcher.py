from datetime import date

import requests
from findpapers.models.paper import Paper
from findpapers.models.publication import Publication
from findpapers.models.search import Search

# from findpapers.tools.references_tool import References

OPENCITATIONS_API = 'https://opencitations.net/index/api/v1/metadata/'
DATABASE_LABEL = 'OC' #short for opencitations
SPLIT_AUTHOR = '; '

def _get_paper_entry(doi: str) -> dict:
    """
    Uses the DOI and extracts the metadata of the paper from Opencitations API.

    Args:
        doi (str): DOI of the paper.

    Returns:
        dict: Paper entry from the Opencitations API.
    """
    req = requests.get(url=OPENCITATIONS_API + doi)
    citations = req.json()[0]
    return citations

def _get_publication(paper_entry: dict) -> Publication:
    """
    Using a paper entry provided, this method builds a publication instance.

    Args:
        paper_entry (dict): Paper entry retrieved from Opencitations API

    Returns:
        Publication: Publication instance.
    """
    publication_title = paper_entry['source_title']

    if publication_title is None or len(publication_title) == 0:
        publication_title = DATABASE_LABEL

    publication_category = 'Preprint' if publication_title is None else None
        
    publication = Publication(publication_title, 
                              category=publication_category)

    return publication

def _get_paper(paper_entry: dict, publication: Publication) -> Paper:
    """
    Using a paper entry provided, this method builds a paper instance.

    Args:
        paper_entry (dict): A paper entry retrieved from Opencitations API.
        publication (Publication): Publication instance associated with the paper.

    Returns:
        Paper: Paper instance.
    """
    paper_title = paper_entry['title']
    paper_abstract = None
    paper_authors = paper_entry['author'].split(SPLIT_AUTHOR)
    paper_publication = publication
    paper_publication_year = int(paper_entry['year'])
    paper_publication_date = date(year=paper_publication_year, month=1, day=1)
    paper_urls = [paper_entry['oa_link']]
    paper_doi = paper_entry['doi']
    paper_citations = paper_entry['citation']
    paper_pages = paper_entry['page']

    paper = Paper(paper_title, paper_abstract, paper_authors, paper_publication,
                  paper_publication_date, paper_urls, paper_doi, paper_citations,
                  pages=paper_pages)
    return paper

def run():
    pass