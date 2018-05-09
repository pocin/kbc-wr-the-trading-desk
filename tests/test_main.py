import pytest
import logging
from ttdwr.writer import main

def test_main_executes(caplog):
    with caplog.at_level(logging.INFO):
        main()
    assert "Hello, world!" in caplog.text
