import os

from hypothesis import (HealthCheck,
                        Verbosity,
                        settings)

on_azure_pipelines = bool(os.getenv('TF_BUILD', False))
on_travis_ci = bool(os.getenv('CI', False))
settings.register_profile('default',
                          max_examples=(settings.default.max_examples // 5
                                        if on_azure_pipelines or on_travis_ci
                                        else settings.default.max_examples),
                          deadline=None,
                          suppress_health_check=[HealthCheck.filter_too_much,
                                                 HealthCheck.too_slow],
                          verbosity=Verbosity(settings.default.verbosity
                                              + on_travis_ci))
