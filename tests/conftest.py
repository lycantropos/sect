import os
import platform

from hypothesis import (HealthCheck,
                        settings)

on_azure_pipelines = bool(os.getenv('TF_BUILD', False))
is_pypy = platform.python_implementation() == 'PyPy'
settings.register_profile('default',
                          max_examples=(settings.default.max_examples
                                        // 2 * (1 + 9 * is_pypy)
                                        if on_azure_pipelines
                                        else settings.default.max_examples),
                          deadline=None,
                          suppress_health_check=[HealthCheck.filter_too_much,
                                                 HealthCheck.too_slow])
