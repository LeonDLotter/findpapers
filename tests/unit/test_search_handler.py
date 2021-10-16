import os
import json
import findpapers
import tempfile
import pytest
from datetime import datetime
from findpapers.models.search import Search
from findpapers.models.paper import Paper
import findpapers.tools.search_runner_tool as search_runner_tool


@pytest.mark.skip(reason="It needs some revision after some tool's refactoring")
def test_save_and_load(search: Search, paper: Paper):

    temp_dirpath = tempfile.mkdtemp()
    temp_filepath = os.path.join(temp_dirpath, 'output.json')

    search.add_paper(paper)
    
    findpapers.save(search, temp_filepath)

    loaded_search = findpapers.load(temp_filepath)

    assert loaded_search.query == search.query
    assert loaded_search.since == search.since
    assert loaded_search.until == search.until
    assert loaded_search.limit == search.limit
    assert loaded_search.limit_per_database == search.limit_per_database
    assert loaded_search.processed_at.strftime('%Y-%m-%d %H:%M:%S') == search.processed_at.strftime('%Y-%m-%d %H:%M:%S')
    assert len(loaded_search.papers) == len(search.papers)


def test_query_format():

    assert search_runner_tool._is_query_ok('([term a] OR [term b])')
    assert search_runner_tool._is_query_ok('[term a] OR [term b]')
    assert search_runner_tool._is_query_ok('[term a] AND [term b]')
    assert search_runner_tool._is_query_ok('[term a] AND NOT ([term b] OR [term c])')
    assert search_runner_tool._is_query_ok('[term a] OR ([term b] AND ([term c] OR [term d]))')
    assert search_runner_tool._is_query_ok('[term a]')
    assert not search_runner_tool._is_query_ok('[term a] OR ([term b] AND ([term c] OR [term d])')
    assert not search_runner_tool._is_query_ok('[term a] or [term b]')
    assert not search_runner_tool._is_query_ok('[term a] and [term b]')
    assert not search_runner_tool._is_query_ok('[term a] and not [term b]')
    assert not search_runner_tool._is_query_ok('([term a] OR [term b]')
    assert not search_runner_tool._is_query_ok('term a OR [term b]')
    assert not search_runner_tool._is_query_ok('[term a] [term b]')
    assert not search_runner_tool._is_query_ok('[term a] XOR [term b]')
    assert not search_runner_tool._is_query_ok('[term a] OR NOT [term b]')
    assert not search_runner_tool._is_query_ok('[] AND [term b]')
    assert not search_runner_tool._is_query_ok('[ ] AND [term b]')
    assert not search_runner_tool._is_query_ok('[ ]')
    assert not search_runner_tool._is_query_ok('[')


def test_query_sanitize():

    assert search_runner_tool._sanitize_query('[term a]    OR     [term b]') == '[term a] OR [term b]'
    assert search_runner_tool._sanitize_query('[term a]    AND     [term b]') == '[term a] AND [term b]'
    assert search_runner_tool._sanitize_query('([term a]    OR     [term b]) AND [term *]') == '([term a] OR [term b]) AND [term *]'
    assert search_runner_tool._sanitize_query('([term a]\nOR\t[term b]) AND [term *]') == '([term a] OR [term b]) AND [term *]'
    assert search_runner_tool._sanitize_query('([term a]\n\n\n\nOR\n\n\n\n[term b]) AND [term *]') == '([term a] OR [term b]) AND [term *]'


@pytest.mark.parametrize('start_date,'
                         'end_date',
                         [(datetime.fromisoformat('2017-01-01').date(),
                           datetime.fromisoformat('2022-01-01').date())])
def test_date_restriction(start_date: datetime.date,
                          end_date: datetime.date):
    """Tests date restrictions of search function using fake data."""
    search = search_runner_tool.search(None,
                                       '[graph]',
                                       start_date,
                                       end_date,
                                       25,
                                       5)

    # test number of fetched papers
    assert len(search.papers) > 0

    # test date restriction
    dates = [v.publication_date for v in search.papers]
    assert min(dates) >= start_date
    assert max(dates) <= end_date


@pytest.mark.parametrize('limit,'
                         'databases,'
                         'publication_type,'
                         'search_string',
                         [(10,
                           ['pubmed'],
                           ['Journal'],
                           '[asd] AND [TEST]'),
                          (5,
                           ['pubmed'],
                           ['Journal'],
                           '[asd] AND [TEST]'),
                          (3,
                           ['arxiv'],
                           ['Preprint'],
                           '[asd] AND [TEST]')])
def test_search(limit: int,
                databases: list,
                publication_type: list,
                search_string: str):
    """Tests search function using fake data."""
    search = search_runner_tool.search(None,
                                       search_string,
                                       None,
                                       None,
                                       limit*len(databases),
                                       limit,
                                       databases,
                                       publication_type)

    # test number of fetched papers
    assert len(search.papers) == limit*len(databases)

    # test publication type
    for paper in search.papers:
        if paper.publication is not None:
            assert paper.publication.category in publication_type
