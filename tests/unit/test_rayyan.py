import pytest
import logging
import findpapers

from datetime import datetime

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize('databases,'
                         'publication_type,'
                         'search_string,'
                         'since,'
                         'until,'
                         'journal,'
                         'publisher,'
                         'authors,'
                         'day,'
                         'month,'
                         'year',
                         [(['arXiv'],
                           ['Preprint'],
                           '[Multitask] AND [Deep Learning]',
                           '2020-01-01',
                           '2022-01-01',
                           'arXiv',
                           None,
                           ['Yiding Wang', 'Zhenyi Wang', 'Chenghao Li',
                            'Yilin Zhang', 'Haizhou Wang'],
                           25,
                           8,
                           2020
                           )])
def test_convert(databases: list,
                 publication_type: list,
                 search_string: str,
                 since: str,
                 until: str,
                 journal: str,
                 publisher: str,
                 authors: list,
                 day: int,
                 month: int,
                 year: int):
    """Tests correct convertion to rayyan"""
    search = findpapers.search(None,
                               search_string,
                               datetime.fromisoformat(since),
                               datetime.fromisoformat(until),
                               1,
                               1,
                               databases,
                               publication_type)
    results = findpapers.RayyanExport(search)

    assert journal == results.rayyan[0].journal
    assert publisher == results.rayyan[0].publisher
    assert authors == results.rayyan[0].authors
    assert day == results.rayyan[0].day
    assert month == results.rayyan[0].month
    assert year == results.rayyan[0].year


def test_generate_rayyan(caplog):
    """Smoke test for empty results"""
    search = findpapers.search(None,
                               '[interacting brains] AND [graphs]',
                               datetime.fromisoformat('2017-01-01'),
                               datetime.fromisoformat('2019-01-01'),
                               1,
                               1,
                               ['arxiv'])
    rayyan = findpapers.RayyanExport(search)

    with caplog.at_level(logging.INFO):
        rayyan.generate_rayyan_csv()
    assert 'Empty results' in caplog.text
