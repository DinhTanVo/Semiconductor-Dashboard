import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data import load_data,enrich
@pytest.fixture(scope='session')
def data():return load_data()
@pytest.fixture(scope='session')
def context(data):return (data,*enrich(data))
