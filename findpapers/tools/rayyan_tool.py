""""
Class to parse search results to a rayyan compatible format.
"""
import logging
import pandas as pd
from dataclasses import dataclass
from typing import List
from findpapers.models.search import Search


@dataclass
class RayyanPaper:
    key: int
    title: str
    authors: List[str]
    journal: str
    issn: str
    day: int
    month: int
    year: int
    volume: int = None
    issue: int = None
    pages: str = None
    publisher: str = None
    pmc_id: str = None
    pubmed_id: str = None
    url: str = None
    abstract: str = None
    notes: str = None


class RayyanExport:
    "Rayyan compatible class"
    def __init__(self,
                 search_results: Search):
        self.search = search_results

    @property
    def rayyan(self) -> list:
        """List of rayyan papers.

        Returns:
            list: search results
        """
        return self.__rayyan

    @property
    def search(self) -> Search:
        """Results of literature search.

        Returns:
            Search: search results
        """
        return self.__search

    @search.setter
    def search(self, search_results):
        if len(search_results.papers) > 0:
            self.__search = search_results
            self._convert_to_rayyan()

    def _convert_to_rayyan(self):
        papers = self.search.papers
        try:
            rayyan = [RayyanPaper(key=i,
                                  title=p.title,
                                  authors=", ".join(p.authors),
                                  journal=p.publication.title,
                                  issn=p.publication.issn,
                                  day=p.publication_date.day,
                                  month=p.publication_date.month,
                                  year=p.publication_date.year,
                                  pages=p.pages,
                                  publisher=p.publication.publisher,
                                  url=list(p.urls)[0])  # get first url
                      for i, p in enumerate(papers, 1)]  # start key from 1
        except Exception:
            logging.warning('Results can not be converted to rayyan',
                            exc_info=True)
        else:
            self.__rayyan = rayyan

    def generate_rayyan_csv(self, file_name: str):
        papers = pd.DataFrame(self.rayyan)
        papers.to_csv(file_name, index=False)
