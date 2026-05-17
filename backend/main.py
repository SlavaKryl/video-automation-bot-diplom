from fastapi import FastAPI

from backend.odoo_client import odoo_client

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/integrations")
async def integrations_status():
    return {
        "odoo": {
            "enabled": odoo_client.is_ready,
        }
    }
