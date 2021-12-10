import logging
import requests

from datetime import date
from findpapers.models.paper import Paper
from findpapers.models.publication import Publication
from findpapers.models.search import Search


CROSSREF_API = 'https://api.crossref.org/works/'
DATABASE_LABEL = 'CR'  # short for opencitations
SPLIT_AUTHOR = '; '


class date_converter(object):

    def __init__(self, date_parts: list):
        self.date_parts = date_parts
        date_functions = {3: '_ymd_date',
                          2: '_ym_date',
                          1: '_y_date'}

        date_getter = date_functions.get(len(date_parts))
        converter = getattr(self, date_getter)
        converter()
        self.date = date(year=self.year,
                         month=self.month,
                         day=self.day)


    def _ymd_date(self):
        """Sets date parts from list"""
        self.year = int(self.date_parts[0])
        self.month = int(self.date_parts[1])
        self.day = int(self.date_parts[2])

    def _ym_date(self):
        """Sets date parts from list with default day"""
        self.year = int(self.date_parts[0])
        self.month = int(self.date_parts[1])
        self.day = 1


    def _y_date(self):
        """Sets date parts from list with default day and month"""
        self.year = int(self.date_parts[0])
        self.month = 1
        self.day = 1


def _get_paper_entry(doi: str) -> dict:
    """
    Uses the DOI and extracts the metadata of the paper from Opencitations API.

    Args:
        doi (str): DOI of the paper.

    Returns:
        dict: Paper entry from the Opencitations API.
    """

    req = requests.get(url=CROSSREF_API + doi)
    citations = req.json()['message']

    return citations


def _get_publication(paper_entry: dict) -> Publication:
    """
    Generates publication instance from a paper entry.

    Args:
        paper_entry (dict): Paper entry retrieved from Opencitations API

    Returns:
        Publication: Publication instance.
    """

    publication_title = paper_entry['container-title'][0]

    if publication_title is None or len(publication_title) == 0:
        publication_title = DATABASE_LABEL

    if paper_entry['type'] == 'journal-article':
        publication_category = 'Journal'
    else:
        publication_category = paper_entry['type']

    publication = Publication(publication_title,
                              issn=paper_entry['ISSN'][0],
                              publisher=paper_entry['publisher'],
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

    paper_title = paper_entry['title'][0]

    paper_abstract = paper_entry.get('abstract')  # ensure null if not exist
    paper_authors = [f"{a.get('given')} {a.get('family')}" for
                     a in paper_entry.get('author')]

    # get publication date
    date_parts = paper_entry.get('published').get('date-parts')
    paper_date = date_converter(date_parts[0])

    paper_urls = paper_entry.get('URL')
    paper_doi = paper_entry.get('DOI')
    paper_pages = paper_entry.get('page')

    paper_references = []
    if paper_entry.get('reference') is not None:
        paper_references = [d.get('URL') for d in paper_entry.get('reference')]

    # note: check if ok i think these are counts
    paper = Paper(paper_title, paper_abstract, paper_authors,
                  publication, paper_date.date,
                  paper_urls, paper_doi,
                  pages=paper_pages, references=paper_references)

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
