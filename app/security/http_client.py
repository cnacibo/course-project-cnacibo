# ADR-003
from typing import Dict, Any,  Optional
import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)


class ResponseTooLargeError(httpx.RequestError):
    pass


class SecureHTTPClient:
    """Безопасный HTTP-клиент с таймаутами, ретраями и лимитами"""
    def __init__(
        self,
        connect_timeout: float = 5.0,
        read_timeout: float = 30.0,
        write_timeout: float = 30.0,
        pool_timeout: float = 10.0,
        max_retries: int = 3,
        max_response_size: int = 50 * 1024 * 1024,
        follow_redirects: bool = True,
    ):
        self.timeout = httpx.Timeout(
            connect=connect_timeout,
            read=read_timeout,
            write=write_timeout,
            pool=pool_timeout
        )
        self.max_retries = max_retries
        self.max_response_size = max_response_size
        self.follow_redirects = follow_redirects

        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _stream_and_limit(self, resp: httpx.Response) -> httpx.Response:
        # проверим заголовок content-length на наличие и валидность
        cl = resp.headers.get("content-length")
        if cl is not None:
            try:
                size = int(cl)
            except (ValueError, TypeError):
                size = None
            if size is not None and size > self.max_response_size:
                raise ResponseTooLargeError(f"Response too large per Content-Length: {size} bytes")

        # читаем частями
        total = 0
        chunks = []
        async for chunk in resp.aiter_bytes():
            total += len(chunk)
            if total > self.max_response_size:
                # выкидываем ошибку
                await resp.aread()
                raise ResponseTooLargeError(f"Response body exceeded limit: {total} bytes")
            chunks.append(chunk)

        content = b"".join(chunks)

        # формируем новый Response
        new_resp = httpx.Response(
            status_code=resp.status_code,
            content=content,
            headers=resp.headers,
            request=resp.request,
            extensions=resp.extensions,
        )
        return new_resp

    async def request(
            self,
            method: str,
            url: str,
            headers: Optional[Dict[str, str]] = None,
            json: Optional[Dict[str, Any]] = None,
            data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = await self._client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json,
                    data=data,
                    params=params,
                )

                if resp.status_code == 429 and attempt < self.max_retries:
                    retry_after = resp.headers.get("Retry-After")
                    wait = None
                    if retry_after:
                        try:
                            wait = int(retry_after)
                        except ValueError:
                            wait = None
                    await resp.aread()
                    if wait:
                        await asyncio.sleep(wait)
                        continue
                    else:
                        await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                        continue

                # проверяем размер
                resp_checked = await self._stream_and_limit(resp)

                # проверяем статус
                resp_checked.raise_for_status()

                logger.info("Request successful (attempt %d): %s %s", attempt, method, url)
                return resp_checked

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                last_exception = e
                logger.warning("Network/timeout (attempt %d/%d): %s — %s", attempt, self.max_retries, url, str(e))

            except httpx.HTTPStatusError as e:
                last_exception = e
                status = e.response.status_code if e.response is not None else None
                logger.warning("HTTP status error %s (attempt %d/%d): %s", status, attempt, self.max_retries, url)

                if 400 <= (status or 0) < 500:
                    raise e

            except ResponseTooLargeError as e:
                logger.warning("Response too large: %s", str(e))
                raise e

            except Exception as e:
                last_exception = e
                logger.warning("Request failed (attempt %d/%d): %s — %s", attempt, self.max_retries, url, str(e))

            # backoff задержка
            if attempt < self.max_retries:
                base = 0.5 * (2 ** (attempt - 1))
                jitter = base * 0.1
                wait_time = base + (jitter * (0.5 - asyncio.get_running_loop().time() % 1))
                await asyncio.sleep(wait_time)

        raise last_exception or httpx.RequestError("All retry attempts failed")

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)
