import httpx
from fastapi import HTTPException


def parse_error_detail(response: httpx.Response) -> object:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Unknown upstream error."
    if isinstance(payload, dict):
        return payload.get("detail", payload)
    return payload


async def request_service(
    client: httpx.AsyncClient,
    method: str,
    base_url: str,
    path: str,
    *,
    params: dict[str, object] | None = None,
    json: dict[str, object] | None = None,
    operation: str,
) -> object:
    url = f"{base_url.rstrip('/')}{path}"
    try:
        response = await client.request(method, url, params=params, json=json)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"{operation}: service unavailable.") from exc

    if response.is_success:
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    detail = parse_error_detail(response)
    status_code = response.status_code if response.status_code < 500 else 502
    raise HTTPException(status_code=status_code, detail=f"{operation}: {detail}")
