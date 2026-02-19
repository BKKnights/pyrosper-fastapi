# pyrosper-fastapi
Pyrosper Fastapi Tools

## Minimalist Example:
```python
from pyrosper_fastapi import PyrosperMiddleware

app.add_middleware(
    PyrosperMiddleware,
    context_class=MyPyrosperContext,
    get_user_id=lambda request: 42,
)
```
