import asyncio

import pytest

from chaosiqagent.utils import raise_if_errored


@pytest.mark.asyncio
async def test_raise_if_errored():

    async def with_exc():
        raise Exception("boom")

    done, pending = await asyncio.wait([
        asyncio.create_task(with_exc())])

    with pytest.raises(Exception):
        raise_if_errored(done, pending)


@pytest.mark.asyncio
async def test_no_raise_if_cancelled():

    async def cancel_me():
        await asyncio.sleep(5)

    t = asyncio.create_task(cancel_me())
    await asyncio.sleep(1)
    t.cancel()
    await asyncio.sleep(1)

    raise_if_errored([t], [])


@pytest.mark.asyncio
async def test_only_log_how_many_pendings():

    async def wait_for_me():
        await asyncio.sleep(2)

    t = asyncio.create_task(wait_for_me())
    raise_if_errored([], [t])
    await asyncio.wait([t])
