from typing import Any, Protocol


class IStrategy(Protocol):
    async def allow(self, *args: Any, **kwargs: Any) -> bool: ...
