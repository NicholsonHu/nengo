import pytest

import nengo.conftest
import nengo.utils.numpy as npext

pytest_plugins = ["pytester"]


def test_seed_fixture(seed):
    """The seed should be the same on all machines"""
    i = (seed - nengo.conftest.TestConfig.test_seed) % npext.maxint
    assert i == 1832276344


@pytest.mark.parametrize("use_ini", (True, False))
@pytest.mark.parametrize("xfail", (True, False))
def test_unsupported(use_ini, xfail, testdir):
    testdir.makefile(".py", test_file="""
        import pytest

        @pytest.mark.parametrize("param", (True, False))
        def test_unsupported(param):
            assert param

        @pytest.mark.parametrize("param", (True, False))
        def test_unsupported_all(param):
            assert False

        def test_supported():
            assert True
        """)

    if use_ini:
        testdir.makefile(".ini", pytest="""
            [pytest]
            nengo_test_unsupported =
                test_file.py:test_unsupported[False]
                    "One unsupported param
                    with multiline comment"
                test_file.py:test_unsupported_all*
                    "Two unsupported params
                    with multiline comment"
            """)

        testdir.makefile(".py", conftest="""
            from nengo.conftest import pytest_runtest_setup, pytest_configure
            """)
    else:
        testdir.makefile(".py", conftest=
            """
            from nengo.conftest import (
                TestConfig, pytest_runtest_setup, pytest_configure)
    
            class MockSimulator(object):
                unsupported = [
                    ('test_file.py:test_unsupported[False]', 
                     'One unsupported param '
                     'with multiline comment'),
                    ('test_file.py:test_unsupported_all*',
                     'Two unsupported params '
                     'with multiline comment'),
                ]
    
            TestConfig.Simulator = MockSimulator
            """)

    args = "-p nengo.tests.options -rsx".split()
    if xfail:
        args.append("--unsupported")
    output = testdir.runpytest(*args)

    output.stdout.fnmatch_lines_random([
        "*One unsupported param with multiline comment",
        "*Two unsupported params with multiline comment",
    ])

    outcomes = output.parseoutcomes()
    if xfail:
        assert outcomes["xfailed"] == 3
        assert "skipped" not in outcomes
    else:
        assert outcomes["skipped"] == 3
        assert "xfailed" not in outcomes
    assert "failed" not in outcomes
    assert outcomes["passed"] == 2
