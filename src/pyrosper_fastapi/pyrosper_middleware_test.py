import asyncio
from typing import TypeVar, Generic
from unittest.mock import AsyncMock

from pyrosper import BaseContext, Symbol
from pyrosper.mock.mock_experiment import MockExperiment
from pyrosper.mock.mock_pyrosper import MockPyrosper
from pyrosper.mock.mock_variant import MockVariant
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.requests import Request
from .pyrosper_middleware import PyrosperMiddleware



value_key = Symbol("value_key")


def my_experiment() -> MockExperiment:
    """
    Messages v1 experiment setup.
    """
    text_variation_a = "Hello one!"
    text_variation_b = "Hello two!"

    return MockExperiment(
        name="mock experiment",
        variants=[
            MockVariant(name="A", picks={value_key: text_variation_a}),
            MockVariant(name="B", picks={value_key: text_variation_b}),
        ],
        is_enabled=True,
    )

class MockPyrosperContext(BaseContext[MockPyrosper]):
    captured_instances = []

    def setup(self):
        mock_pyrosper = MockPyrosper().with_experiment(my_experiment())
        self.captured_instances.append(mock_pyrosper)
        return mock_pyrosper

def test_middleware_sync_user_id():
    def get_user_id(request: Request):
        return "user_123"

    MockPyrosperContext.captured_instances.clear()

    app = Starlette()
    app.add_middleware(
        PyrosperMiddleware,
        context_class=MockPyrosperContext,
        get_user_id=get_user_id
    )
    
    async def homepage(request):
        return JSONResponse({"hello": "world"})
    
    app.add_route("/", homepage)

    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}
    assert len(MockPyrosperContext.captured_instances) == 1
    assert MockPyrosperContext.captured_instances[0].get_experiment("mock experiment").user_id == "user_123"

def test_middleware_async_user_id():
    async def get_user_id(request: Request):
        await asyncio.sleep(0.01)
        return "user_async_456"

    MockPyrosperContext.captured_instances.clear()

    app = Starlette()
    app.add_middleware(
        PyrosperMiddleware,
        context_class=MockPyrosperContext,
        get_user_id=get_user_id
    )

    async def homepage_async(request):
        return JSONResponse({"status": "ok"})
    
    app.add_route("/", homepage_async)

    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert len(MockPyrosperContext.captured_instances) == 1
    assert MockPyrosperContext.captured_instances[0].get_experiment("mock experiment").user_id == "user_async_456"

def test_middleware_no_user_id():
    def get_user_id(request: Request):
        return None

    MockPyrosperContext.captured_instances.clear()

    app = Starlette()
    app.add_middleware(
        PyrosperMiddleware,
        context_class=MockPyrosperContext,
        get_user_id=get_user_id
    )

    async def homepage_no_user(request):
        return JSONResponse({"status": "ok"})
    
    app.add_route("/", homepage_no_user)

    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert len(MockPyrosperContext.captured_instances) == 1
    # No user_id set, should not have user_id attribute or it should be default
    experiment = MockPyrosperContext.captured_instances[0].get_experiment("mock experiment")
    assert not hasattr(experiment, "user_id")

def test_middleware_exception_in_handler():
    def get_user_id(request: Request):
        return "user_789"

    MockPyrosperContext.captured_instances.clear()

    app = Starlette()
    app.add_middleware(
        PyrosperMiddleware,
        context_class=MockPyrosperContext,
        get_user_id=get_user_id
    )

    async def homepage_error(request):
        raise ValueError("Something went wrong")
    
    app.add_route("/", homepage_error)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/")
    
    assert response.status_code == 500
    assert len(MockPyrosperContext.captured_instances) == 1
    assert MockPyrosperContext.captured_instances[0].get_experiment("mock experiment").user_id == "user_789"

def test_middleware_async_set_for_user():
    def get_user_id(request: Request):
        return "user_abc"

    MockPyrosperContext.captured_instances.clear()

    app = Starlette()
    app.add_middleware(
        PyrosperMiddleware,
        context_class=MockPyrosperContext,
        get_user_id=get_user_id
    )
    
    async def homepage(request):
        return JSONResponse({"ok": True})
    
    app.add_route("/", homepage)

    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    assert len(MockPyrosperContext.captured_instances) == 1
    assert MockPyrosperContext.captured_instances[0].get_experiment("mock experiment").user_id == "user_abc"
