import httpx


class TestClient(httpx.AsyncClient):
    async def get(self, *args, **kwargs) -> httpx.Response:
        return httpx.Response(
            status_code=200, request=httpx.Request("GET", args[0]),
            content=b'{"msg": "hello"}')
