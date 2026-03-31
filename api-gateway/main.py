import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response

SERVICE_CONFIG = {
    "cargo": {
        "service_url": os.getenv("CARGO_SERVICE_URL", "http://localhost:8081"),
        "resource_path": "/cargo",
    },
    "locations": {
        "service_url": os.getenv("LOCATION_SERVICE_URL", "http://localhost:8082"),
        "resource_path": "/locations",
    },
    "inventory-items": {
        "service_url": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8083"),
        "resource_path": "/inventory-items",
    },
    "suppliers": {
        "service_url": os.getenv("SUPPLIER_SERVICE_URL", "http://localhost:8084"),
        "resource_path": "/suppliers",
    },
    "staff": {
        "service_url": os.getenv("STAFF_SERVICE_URL", "http://localhost:8085"),
        "resource_path": "/staff",
    },
    "equipment": {
        "service_url": os.getenv("EQUIPMENT_SERVICE_URL", "http://localhost:8086"),
        "resource_path": "/equipment",
    },
}

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

app = FastAPI(
    title="Warehouse API Gateway",
    version="1.0.0",
    description="Single entrypoint for the warehouse microservices.",
)


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "gateway": "warehouse-api-gateway",
        "database": "PostgreSQL",
        "service_routes": {name: f"/{name}" for name in SERVICE_CONFIG},
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict[str, object]:
    results: dict[str, dict[str, object]] = {}

    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, config in SERVICE_CONFIG.items():
            try:
                response = await client.get(f"{config['service_url'].rstrip('/')}/health")
                results[name] = {
                    "status": "up" if response.is_success else "degraded",
                    "status_code": response.status_code,
                }
            except httpx.RequestError as exc:
                results[name] = {"status": "down", "error": str(exc)}

    overall = "healthy" if all(item["status"] == "up" for item in results.values()) else "degraded"
    return {"gateway": "healthy", "overall": overall, "services": results}

# --- NEW:
@app.get("/services/docs")
async def docs_index() -> dict[str, object]:
    return {
        "gateway_docs": "/docs",
        "service_docs_via_gateway": {
            name: f"/{name}/docs" for name in SERVICE_CONFIG
        },
        "service_openapi_via_gateway": {
            name: f"/{name}/openapi.json" for name in SERVICE_CONFIG
        },
    }


@app.get("/{service}/docs", include_in_schema=False)
async def service_docs_via_gateway(service: str):
    if service not in SERVICE_CONFIG:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'.")

    return get_swagger_ui_html(
        openapi_url=f"/{service}/openapi.json",
        title=f"{service.title()} Service Docs (via Gateway)",
    )


@app.get("/{service}/openapi.json", include_in_schema=False)
async def service_openapi_via_gateway(service: str) -> Response:
    config = SERVICE_CONFIG.get(service)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'.")

    target_url = f"{config['service_url'].rstrip('/')}/openapi.json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            upstream = await client.get(target_url)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"{service} service unavailable: {exc}") from exc

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
# --- END NEW ---

async def forward_request(service: str, path: str, request: Request) -> Response:
    config = SERVICE_CONFIG.get(service)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'.")

    target_path = "/health" if path == "health" else config["resource_path"]
    if path and path != "health":
        target_path = f"{config['resource_path']}/{path}"

    target_url = f"{config['service_url'].rstrip('/')}{target_path}"
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length"}
    }
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                request.method,
                target_url,
                params=request.query_params,
                content=body or None,
                headers=headers,
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"{service} service unavailable: {exc}") from exc

    media_type = upstream.headers.get("content-type")
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=media_type,
    )


@app.api_route("/{service}", methods=HTTP_METHODS)
async def proxy_collection(service: str, request: Request) -> Response:
    return await forward_request(service, "", request)


@app.api_route("/{service}/{path:path}", methods=HTTP_METHODS)
async def proxy_detail(service: str, path: str, request: Request) -> Response:
    return await forward_request(service, path, request)
