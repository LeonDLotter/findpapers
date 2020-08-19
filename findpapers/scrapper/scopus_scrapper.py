import requests
import datetime
import logging
import re
from lxml import html
from typing import Optional
from fake_useragent import UserAgent
import findpapers.util as util
from findpapers.models.search import Search
from findpapers.models.paper import Paper
from findpapers.models.publication import Publication
from findpapers.models.bibliometrics import ScopusBibliometrics

logger = logging.getLogger(__name__)

AREAS_BY_KEY = {
    'computer_science': ['COMP', 'MULT'],
    'economics': ['ECON', 'BUSI', 'MULT'],
    'engineering': ['AGRI', 'CENG', 'ENER', 'ENGI', 'ENVI', 'MATE', 'MULT'],
    'mathematics': ['MATH', 'MULT'],
    'physics': ['EART', 'PHYS', 'MULT'],
    'biology': ['AGRI', 'BIOC', 'DENT', 'ENVI', 'HEAL', 'IMMU', 'MEDI', 'NEUR', "NURS", 'PHAR', 'VETE', 'MULT'],
    'chemistry': ['CENG', 'CHEM', 'PHAR', 'MULT'],
    'humanities': ['ARTS', 'DECI', 'ENVI', 'PSYC', 'SOCI', 'MULT']
}


def get_query(search: Search) -> str:
    """
    Get the translated query from search instance to fetch data from Scopus database
    See https://dev.elsevier.com/tips/ScopusSearchTips.htm for query tips

    Parameters
    ----------
    search : Search
        A search instance

    Returns
    -------
    str
        The translated query
    """

    query = f'TITLE-ABS-KEY({search.query})'

    if search.since is not None:
        query += f' AND PUBYEAR > {search.since.year - 1}'

    if search.areas != None:
        selected_areas = []
        for area in search.areas:
            scopus_areas = AREAS_BY_KEY.get(area, [])
            for scopus_area in scopus_areas:
                selected_areas.append(scopus_area)
        if len(selected_areas) > 0:
            query += f' AND SUBJAREA({" OR ".join(selected_areas)})'

    return query


def get_publication(paper_entry: dict, api_token: str) -> Publication:
    """
    Using a paper entry provided, this method builds a publication instance

    Parameters
    ----------
    paper_entry : dict
        A paper entry retrived from scopus API
    api_token : str
        A Scopus API token

    Returns
    -------
    Publication
        A publication instance
    """

    # getting data

    publication_title = paper_entry.get('prism:publicationName', None)
    publication_isbn = paper_entry.get('prism:isbn', None)
    publication_issn = paper_entry.get('prism:issn', None)
    publication_category = paper_entry.get('prism:aggregationType', None)
    publication_publisher = None
    publication_cite_score = None
    publication_sjr = None
    publication_snip = None

    # post processing data

    if isinstance(publication_isbn, list):
        publication_isbn = publication_isbn[0]['$']

    if isinstance(publication_issn, list):
        publication_issn = publication_issn[0]['$']

    # enriching data

    if publication_issn is not None:

        url = f'https://api.elsevier.com/content/serial/title/issn/{publication_issn}?apiKey={api_token}'
        headers = {'User-Agent': str(UserAgent().chrome),
                   'Accept': 'application/json'}
        response = util.try_success(lambda: requests.get(
            url, headers=headers).json()['serial-metadata-response'], 5)

        if response is not None and 'entry' in response and len(response['entry']) > 0:

            publication_entry = response['entry'][0]

            publication_publisher = publication_entry.get('dc:publisher', None)

            publication_cite_score = util.try_success(lambda: float(
                publication_entry['citeScoreYearInfoList']['citeScoreCurrentMetric']))

            if 'SJRList' in publication_entry and len(publication_entry['SJRList']['SJR']) > 0:
                publication_sjr = util.try_success(lambda: float(
                    publication_entry['SJRList']['SJR'][0]['$']))

            if 'SNIPList' in publication_entry and len(publication_entry['SNIPList']['SNIP']) > 0:
                publication_snip = util.try_success(lambda: float(
                    publication_entry['SNIPList']['SNIP'][0]['$']))

    publication = Publication(publication_title, publication_isbn,
                              publication_issn, publication_publisher, publication_category)

    if publication_cite_score is not None or publication_sjr is not None or publication_snip is not None:

        scopus_bibliometrics = ScopusBibliometrics(
            publication_cite_score, publication_sjr, publication_snip)
        publication.add_bibliometrics(scopus_bibliometrics)

    return publication


def get_paper(paper_entry: dict, publication: Publication) -> Paper:
    """
    Using a paper entry provided, this method builds a paper instance

    Parameters
    ----------
    paper_entry : dict
        A paper entry retrived from scopus API
    publication : Publication
        A publication instance that will be associated with the paper

    Returns
    -------
    Paper
        A paper instance
    """

    # getting data

    paper_title = paper_entry.get('dc:title', None)
    paper_publication_date = paper_entry.get('prism:coverDate', None)
    paper_doi = paper_entry.get('prism:doi', None)
    paper_citations = paper_entry.get('citedby-count', None)
    paper_first_author = paper_entry.get('dc:creator', None)
    paper_abstract = None
    paper_authors = []
    paper_urls = set()
    paper_keywords = set()

    # post processing data

    if paper_first_author is not None:
        paper_authors.append(paper_first_author)

    if paper_publication_date is not None:
        date_split = paper_publication_date.split('-')
        paper_publication_date = datetime.date(
            int(date_split[0]), int(date_split[1]), int(date_split[2]))

    if paper_citations is not None:
        paper_citations = int(paper_citations)

    # enriching data

    paper_scopus_link = None
    for link in paper_entry.get('link', []):
        if link.get('@ref') == 'scopus':
            paper_scopus_link = link.get('@href')
            break

    if paper_scopus_link is not None:

        paper_urls.add(paper_scopus_link)

        try:

            response = util.try_success(lambda: requests.get(
                paper_scopus_link, headers={'User-Agent': str(UserAgent().chrome)}), 5)
            paper_page = html.fromstring(response.content.decode('UTF-8'))

            try:
                paper_abstract = paper_page.xpath(
                    '//section[@id="abstractSection"]//p//text()[normalize-space()]')
                paper_abstract = re.sub(
                    '\xa0', ' ', ''.join(paper_abstract)).strip()
            except Exception as e:
                logging.warning(
                    'An attempt to collect the abstract has failed')

            try:
                authors = paper_page.xpath(
                    '//*[@id="authorlist"]/ul/li/span[@class="previewTxt"]')
                paper_authors = []
                for author in authors:
                    paper_authors.append(author.text.strip())
            except Exception as e:
                logging.warning('An attempt to collect the authors has failed')

            try:
                keywords = paper_page.xpath('//*[@id="authorKeywords"]/span')
                for keyword in keywords:
                    paper_keywords.add(keyword.text.strip())
            except Exception as e:
                logging.warning(
                    'An attempt to collect the keywords has failed')

        except Exception as e:
            logging.error(e)

    paper = Paper(paper_title, paper_abstract, paper_authors, publication,
                  paper_publication_date, paper_urls, paper_doi, paper_citations, paper_keywords)

    return paper


def run(search: Search, api_token: str, url: Optional[str] = None):
    """
    This method fetch papers from Scopus database using the provided search parameters
    After fetch the data from Scopus, the collected papers are added to the provided search instance

    Parameters
    ----------
    search : Search
        A search instance
    api_token : str
        The API key used to fetch data from Scopus database,
    url : Optional[str]
        A predefined URL to be used for the search execution, 
        this is usually used for make the next recursive call on a result pagination

    Raises
    ------
    AttributeError
        - The API token cannot be null
    """

    if api_token is None or len(api_token.strip()) == 0:
        raise AttributeError('The API token cannot be null')
    
    # is url is not None probably this is a recursive call to the next url of a pagination
    if url is None:
        query = get_query(search)
        url = f'https://api.elsevier.com/content/search/scopus?&sort=citedby-count,relevancy,pubyear&apiKey={api_token}&query={query}'
    
    headers = {'User-Agent': str(UserAgent().chrome),
               'Accept': 'application/json'}

    response = util.try_success(lambda: requests.get(
        url, headers=headers).json()['search-results'], 5)

    total_papers = response.get('opensearch:totalResults', 0)
    start_pagination_index = int(response.get('opensearch:startIndex', 0))
    processed_papers = 0

    logging.info(f'{total_papers} papers retrived')

    for paper_entry in response.get('entry', []):

        if search.limit is not None and len(search.papers) >= search.limit:
            break

        try:
            logging.info(paper_entry.get("dc:title", None))

            publication = get_publication(paper_entry, api_token)
            paper = get_paper(paper_entry, publication)
            paper.add_library('Scopus')

            search.add_paper(paper)

        except Exception as e:
            logging.error(e)

        processed_papers += 1
        logging.info(f'{processed_papers+start_pagination_index}/{total_papers} papers fetched')

    next_url = None
    for link in response['link']:
        if link['@ref'] == 'next':
            next_url = link['@href']
            break
        
    # If there is a next url, the API provided response was paginated and we need to process the next url
    # We'll make a recursive call for it
    if next_url is not None and search.limit is None or len(search.papers) < search.limit:
        run(search, api_token, next_url)
