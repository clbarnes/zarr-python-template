from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def fixture_dpath():
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def data():
    return np.arange(150, dtype="float32").reshape((10, 15))
