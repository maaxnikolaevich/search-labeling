from __future__ import annotations

import os

from keycloak import KeycloakOpenID

keycloak_client = KeycloakOpenID(
    server_url=os.getenv("KEYCLOAK_URL") or "",
    client_id=os.getenv("KEYCLOAK_CLIENT") or "",
    realm_name=os.getenv("KEYCLOAK_REALM") or "",
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
)
