import pytest
import logging
import findpapers

from datetime import datetime

LOGGER = logging.getLogger(__name__)


def test_smoke_generate_rayyan_csv(caplog):
    """Smoke test for empty results"""
    search = findpapers.search(None,
                               '[interacting brains] AND [graphs]',
                               datetime.fromisoformat('2017-01-01').date,
                               datetime.fromisoformat('2019-01-01').date,
                               1,
                               1,
                               ['arxiv'])
    rayyan = findpapers.RayyanExport(search)

    with caplog.at_level(logging.INFO):
        rayyan.generate_rayyan_csv('test.csv')
    assert 'Empty results' in caplog.text
