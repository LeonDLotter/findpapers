from typing import List, Optional
from datetime import date


class Bibliometrics():
    """
    Bibliometrics base class
    """

    def __init__(self, source_name: str):
        """
        Bibliometrics constructor

        Parameters
        ----------
        source_name : str
            The source name of the service where metrics came from
        """
        self.source_name = source_name


class ScopusBibliometrics(Bibliometrics):
    """
    ScopusBibliometrics class
    """

    def __init__(self, cite_score: Optional[float] = None, sjr: Optional[float] = None, snip: Optional[float] = None):
        """
        ScopusBibliometrics class constructor

        Parameters
        ----------
        cite_score : float
            CiteScore measures average citations received per document published in the serial
        sjr : float
            SCImago Journal Rank measures weighted citations received by the serial. Citation weighting depends on subject field and prestige (SJR) of the citing serial, by default None
        snip: float
            Source Normalized Impact per Paper measures actual citations received relative to citations expected for the serial’s subject field, by default None
        """

        super().__init__('Scopus')

        self.cite_score = cite_score
        self.sjr = sjr
        self.snip = snip
