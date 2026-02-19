

import inspect
from contextlib import AbstractContextManager
from typing import Callable, Optional, Awaitable, Union, Type, TypeVar

from pyrosper import Pyrosper
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

PyrosperType = TypeVar("PyrosperType", bound="Pyrosper")
PyrosperContextType = Type[AbstractContextManager[PyrosperType]]

class PyrosperMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        context_class: PyrosperContextType,
        get_user_id: Callable[[Request], Union[Optional[str], Awaitable[Optional[str]]]],
    ):
        super().__init__(app)
        self.get_user_id = get_user_id
        self.context_class = context_class

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        user_id_or_possible_promise = self.get_user_id(request)
        if inspect.isawaitable(user_id_or_possible_promise):
            user_id = await user_id_or_possible_promise
        else:
            user_id = user_id_or_possible_promise

        with self.context_class() as pyrosper:
            if user_id:
                await pyrosper.set_for_user(user_id)
            return await call_next(request)

