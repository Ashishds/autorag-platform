"""OAuth flows for third-party integrations."""

from __future__ import annotations

import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
from urllib.parse import urlencode

from app.config import settings
from app.dependencies import get_connector_service
from app.services.connector_service import ConnectorService
from app.schemas.connector import ConnectorUpdate

router = APIRouter()

@router.get("/{connector_id}/{provider}/authorize")
async def authorize(
    connector_id: UUID,
    provider: str,
    token: str | None = None,
    svc: ConnectorService = Depends(get_connector_service),
):
    connector = await svc.get(connector_id)
    if not connector:
        raise HTTPException(404, "Connector not found")
        
    org_id = UUID(int=0)
    actor_id = UUID(int=0)
    
    if token:
        try:
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            if "org_id" in decoded:
                org_id = UUID(decoded["org_id"])
            elif "user_metadata" in decoded and "org_id" in decoded["user_metadata"]:
                org_id = UUID(decoded["user_metadata"]["org_id"])
            elif "app_metadata" in decoded and "org_id" in decoded["app_metadata"]:
                org_id = UUID(decoded["app_metadata"]["org_id"])
            if "sub" in decoded:
                actor_id = UUID(decoded["sub"])
        except Exception:
            pass

    # Verify that the connector belongs to the organization (unless it's mock tenant)
    if org_id != UUID(int=0) and connector.get("organization_id") != org_id:
        raise HTTPException(403, "Access denied: Connector does not belong to this organization")
        
    redirect_uri = f"{settings.APP_BASE_URL}{settings.API_V1_PREFIX}/oauth/{provider}/callback"
    
    # Sign state token using jwt to ensure callback payload authenticity
    import jwt
    import time
    signing_key = settings.SUPABASE_SERVICE_ROLE_KEY or "local-dev-secret"
    state_payload = {
        "connector_id": str(connector_id),
        "org_id": str(org_id),
        "actor_id": str(actor_id),
        "exp": int(time.time()) + 600  # 10 minutes expiry
    }
    state = jwt.encode(state_payload, signing_key, algorithm="HS256")
    
    if provider == "google_drive":
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/drive.readonly",
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return RedirectResponse(url)
        
    elif provider == "notion":
        params = {
            "client_id": settings.NOTION_CLIENT_ID,
            "response_type": "code",
            "owner": "user",
            "redirect_uri": redirect_uri,
            "state": state
        }
        url = f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"
        return RedirectResponse(url)
        
    elif provider == "dropbox":
        params = {
            "client_id": settings.DROPBOX_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state
        }
        url = f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"
        return RedirectResponse(url)
        
    elif provider == "microsoft":
        params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "offline_access Files.Read.All Sites.Read.All",
            "state": state
        }
        url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
        return RedirectResponse(url)
        
    raise HTTPException(400, "Unsupported provider")


@router.get("/{provider}/callback")
async def callback(
    provider: str,
    code: str,
    state: str,
    svc: ConnectorService = Depends(get_connector_service),
):
    try:
        org_id = UUID(int=0)
        actor_id = UUID(int=0)
        signing_key = settings.SUPABASE_SERVICE_ROLE_KEY or "local-dev-secret"
        
        try:
            import jwt
            decoded_state = jwt.decode(state, signing_key, algorithms=["HS256"])
            connector_id = UUID(decoded_state["connector_id"])
            org_id = UUID(decoded_state["org_id"])
            actor_id = UUID(decoded_state["actor_id"])
        except Exception:
            # Fallback to direct state validation for local dev/backwards compatibility
            try:
                connector_id = UUID(state)
            except ValueError:
                return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?auth_status=error&error=Invalid+state+parameter")

        connector = await svc.get(connector_id)
        if not connector:
            return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?auth_status=error&error=Connector+not+found")
            
        # Verify ownership (unless it's mock tenant)
        if org_id != UUID(int=0) and connector.get("organization_id") != org_id:
            return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?auth_status=error&error=Access+denied")
            
        redirect_uri = f"{settings.APP_BASE_URL}{settings.API_V1_PREFIX}/oauth/{provider}/callback"
        config_update = connector.get("config", {})
        
        async with httpx.AsyncClient() as client:
            if provider == "google_drive":
                token_data = {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
                resp = await client.post("https://oauth2.googleapis.com/token", data=token_data)
                if resp.status_code != 200:
                    raise ValueError(f"Google OAuth failed: {resp.text}")
                
                tokens = resp.json()
                config_update["oauth_tokens"] = tokens
                
            elif provider == "notion":
                import base64
                auth_str = f"{settings.NOTION_CLIENT_ID}:{settings.NOTION_CLIENT_SECRET}"
                b64_auth = base64.b64encode(auth_str.encode()).decode()
                
                headers = {
                    "Authorization": f"Basic {b64_auth}",
                    "Content-Type": "application/json"
                }
                token_data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri
                }
                resp = await client.post("https://api.notion.com/v1/oauth/token", json=token_data, headers=headers)
                if resp.status_code != 200:
                    raise ValueError(f"Notion OAuth failed: {resp.text}")
                    
                tokens = resp.json()
                config_update["oauth_tokens"] = tokens
                
            elif provider == "dropbox":
                token_data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.DROPBOX_CLIENT_ID,
                    "client_secret": settings.DROPBOX_CLIENT_SECRET,
                    "redirect_uri": redirect_uri
                }
                resp = await client.post("https://api.dropboxapi.com/oauth2/token", data=token_data)
                if resp.status_code != 200:
                    raise ValueError(f"Dropbox OAuth failed: {resp.text}")
                tokens = resp.json()
                config_update["oauth_tokens"] = tokens
                
            elif provider == "microsoft":
                token_data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "redirect_uri": redirect_uri
                }
                resp = await client.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=token_data)
                if resp.status_code != 200:
                    raise ValueError(f"Microsoft OAuth failed: {resp.text}")
                tokens = resp.json()
                config_update["oauth_tokens"] = tokens
                
            else:
                return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?auth_status=error&error=Unsupported+provider")
                
        update_data = ConnectorUpdate(config=config_update)
        await svc.update(connector_id, update_data, actor_id=actor_id, organization_id=org_id)
        
        # Trigger automatic sync immediately on successful authorization
        await svc.trigger_sync(connector_id, actor_id=actor_id, organization_id=org_id)
        
        return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?auth_status=success&connector_id={connector_id}")
        
    except Exception as e:
        import urllib.parse
        err_msg = urllib.parse.quote(str(e))
        return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?auth_status=error&error={err_msg}")
