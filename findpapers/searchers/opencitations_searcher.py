import logging
import requests

from datetime import date
from findpapers.models.paper import Paper
from findpapers.models.publication import Publication
from findpapers.models.search import Search

# from findpapers.tools.references_tool import References

OPENCITATIONS_API = 'https://opencitations.net/index/api/v1/metadata/'
DATABASE_LABEL = 'OC'  # short for opencitations
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
    Generates publication instance from a paper entry.

    Args:
        paper_entry (dict): Paper entry retrieved from Opencitations API

    Returns:
        Publication: Publication instance.
    """

    publication_title = paper_entry['source_title']

    if publication_title is None or len(publication_title) == 0:
        publication_title = DATABASE_LABEL

    # publication_category = 'Preprint' if publication_title is None else None
    publication_category = None

    publication = Publication(publication_title,
                              category=publication_category)

    return publication


def _get_paper(paper_entry: dict, publication: Publication) -> Paper:
    """
    Creates paper instance from paper entry.

    Args:
        paper_entry (dict): A paper entry retrieved from Opencitations API.
        publication (Publication): Publication instance associated
            with the paper.

    Returns:
        Paper: Paper instance.
    """

    paper_title = paper_entry['title']
    paper_abstract = None
    paper_authors = paper_entry['author'].split(SPLIT_AUTHOR)
    paper_publication_year = int(paper_entry['year'])
    paper_publication_date = date(year=paper_publication_year, month=1, day=1)
    paper_urls = [paper_entry['oa_link']]
    paper_doi = paper_entry['doi']
    paper_pages = paper_entry['page']
    paper_citations_count = paper_entry['citation_count']

    paper_citations = []
    paper_references = []

    # add cross references as a list of clean DOIs
    if len(paper_entry['citation']) > 0:
        paper_citations = paper_entry['citation'].replace(' ', '').split(';')
    if len(paper_entry['reference']) > 0:
        paper_references = paper_entry['reference'].replace(' ', '').split(';')

    # note: check if ok i think these are counts
    paper = Paper(paper_title, paper_abstract, paper_authors,
                  publication, paper_publication_date,
                  paper_urls, paper_doi, paper_citations_count,
                  pages=paper_pages, references=paper_references,
                  cites=paper_citations)

    return paper


def _add_papers(search: Search, source: str):
    # get references/citations
    source_dois = [d for s, p in search.paper_by_doi.items()
                   for d in getattr(p, source)]

    # gather paper metadata
    if len(source_dois) > 0:
        for doi in source_dois:
            paper_entry = _get_paper_entry(doi)
            publication = _get_publication(paper_entry)
            paper = _get_paper(paper_entry, publication)

            if paper is not None:
                paper.source = source
                paper.add_database(DATABASE_LABEL)
                search.add_paper(paper)


def run(search: Search, references: bool = True, citations: bool = True):

    try:
        if references:
            _add_papers(search, 'references')
        if citations:
            _add_papers(search, 'cites')
    except Exception as e:
        logging.debug(e, exc_info=True)
