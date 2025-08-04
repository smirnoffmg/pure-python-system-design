import asyncio

import pytest

from url_shortener.infrastructure import BaseStorage


@pytest.mark.asyncio
async def test_storage_idempt(storage: BaseStorage):
    short_url_1 = await storage.create_short_code("google.com")
    short_url_2 = await storage.create_short_code("google.com")
    assert short_url_1 == short_url_2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_url", ["google.com", "123123123.com", "url-with-symbols.com"]
)
async def test_storage_equiv(test_url: str, storage: BaseStorage):
    short_url = await storage.create_short_code(test_url)
    full_url = await storage.get_full_url(short_url)
    assert test_url == full_url, f"{test_url} != {full_url}"


@pytest.mark.asyncio
@pytest.mark.parametrize("tasks_n", [1, 10, 100, 500])
async def test_concurrent_operations(storage: BaseStorage, tasks_n: int):
    tasks = [
        storage.create_short_code(f"http://example.com/{i}") for i in range(tasks_n)
    ]
    results = await asyncio.gather(*tasks)

    assert len(set(results)) == len(results)
