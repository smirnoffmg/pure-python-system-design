import pytest

from url_shortener.application import BaseShortener


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    "test_url", ["google.com", "123123123.com", "url-with-symbols.com"]
)
async def test_svc_equiv(test_url: str, svc: BaseShortener):
    short_url = await svc.create_short_code(test_url)
    full_url = await svc.get_full_url(short_url)
    assert test_url == full_url, f"{test_url} != {full_url}"


@pytest.mark.asyncio()
async def test_svc_non_existing_url(svc: BaseShortener):
    assert await svc.get_full_url("non-existing-entry") is None
