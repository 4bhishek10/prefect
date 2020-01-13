import pytest

import prefect
from prefect.engine.cloud.utilities import prepare_state_for_cloud
from prefect.engine.result import NoResult, Result, SafeResult
from prefect.engine.result_handlers import JSONResultHandler, ResultHandler
from prefect.engine.state import Cached, Failed, Pending, Success, _MetaState

all_states = sorted(
    set(
        cls
        for cls in prefect.engine.state.__dict__.values()
        if isinstance(cls, type)
        and issubclass(cls, prefect.engine.state.State)
        and not cls is _MetaState
    ),
    key=lambda c: c.__name__,
)


@pytest.mark.parametrize("cls", [s for s in all_states if s.__name__ != "State"])
def test_preparing_state_for_cloud_replaces_cached_inputs_with_safe(cls):
    xres = Result(3, result_handler=JSONResultHandler())
    state = prepare_state_for_cloud(cls(cached_inputs=dict(x=xres)))
    assert isinstance(state, cls)
    assert state.result is None
    assert state._result == NoResult
    assert state.cached_inputs == dict(x=xres)
    assert state.serialize()["cached_inputs"]["x"]["value"] == "3"


@pytest.mark.parametrize("cls", [s for s in all_states if s.__name__ != "State"])
def test_preparing_state_for_cloud_ignores_the_lack_of_result_handlers_for_cached_inputs(
    cls,
):
    xres = Result(3, result_handler=None)
    state = prepare_state_for_cloud(cls(cached_inputs=dict(x=xres)))
    assert isinstance(state, cls)
    assert state.result is None
    assert state._result == NoResult
    assert state.cached_inputs == dict(x=xres)
    assert state.serialize()["cached_inputs"]["x"]["type"] == "NoResultType"


@pytest.mark.parametrize("cls", [s for s in all_states if s.__name__ != "State"])
def test_preparing_state_for_cloud_does_nothing_if_result_is_none(cls):
    xres = Result(None, result_handler=JSONResultHandler())
    state = prepare_state_for_cloud(cls(cached_inputs=dict(x=xres)))
    assert isinstance(state, cls)
    assert state.result is None
    assert state._result == NoResult
    assert state.cached_inputs == dict(x=xres)
    assert state.serialize()["cached_inputs"]["x"]["type"] == "NoResultType"


@pytest.mark.skip(reason="Result Handlers are not required to exist currently")
@pytest.mark.parametrize("cls", [s for s in all_states if s.__name__ != "State"])
def test_preparing_state_for_cloud_fails_if_cached_inputs_have_no_handler(cls):
    xres = Result(3, result_handler=None)
    with pytest.raises(AssertionError, match="no ResultHandler"):
        state = prepare_state_for_cloud(cls(cached_inputs=dict(x=xres)))


def test_preparing_state_for_cloud_doesnt_copy_data():
    class FakeHandler(ResultHandler):
        def read(self, val):
            return val

        def write(self, val):
            return val

    value = 124.090909
    result = Result(value, result_handler=FakeHandler())
    state = Cached(result=result)
    cloud_state = prepare_state_for_cloud(state)
    assert cloud_state.is_cached()
    assert cloud_state.result is state.result
