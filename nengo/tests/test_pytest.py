import pytest

import nengo.conftest
import nengo.utils.numpy as npext

pytest_plugins = ["pytester"]


def test_seed_fixture(seed):
    """The seed should be the same on all machines"""
    i = (seed - nengo.conftest.TestConfig.test_seed) % npext.maxint
    assert i == 1832276344


@pytest.mark.parametrize("xfail", (True, False))
def test_unsupported(xfail, testdir):
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


def test_pyargs(testdir):
    # create a simulator that immediately fails (we don't actually want
    # to run all the tests)
    testdir.makeconftest(
        """
        import nengo.conftest

        class MockSimulator(object):
            pass

        nengo.conftest.TestConfig.Simulator = MockSimulator
        """)

    # mark all the tests as unsupported
    testdir.makefile(".ini", pytest="""
        [pytest]
        nengo_test_unsupported =
            *
                "Using mock simulator"
        """)

    try:
        outcomes = testdir.runpytest(
            "-p", "nengo.tests.options",
            "--pyargs", "nengo",
            "--unsupported",
        ).parseoutcomes()
    finally:
        # runpytest runs in-process, so we have to undo changes to TestConfig
        nengo.conftest.TestConfig.Simulator = nengo.Simulator

    assert "failed" not in outcomes
    assert "passed" not in outcomes
    assert outcomes["xfailed"] > 350
    assert outcomes["deselected"] > 700
