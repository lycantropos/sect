import os
from decimal import getcontext

import pytest
from hypothesis import (HealthCheck,
                        settings)

from tests.utils import MAX_COORDINATE_EXPONENT

on_azure_pipelines = bool(os.getenv('TF_BUILD', False))
settings.register_profile('default',
                          max_examples=(settings.default.max_examples // 5
                                        if on_azure_pipelines
                                        else settings.default.max_examples),
                          deadline=None,
                          suppress_health_check=[HealthCheck.filter_too_much,
                                                 HealthCheck.too_slow])


@pytest.fixture(autouse=True,
                scope='session')
def set_decimal_context() -> None:
    getcontext().prec = MAX_COORDINATE_EXPONENT * 3
