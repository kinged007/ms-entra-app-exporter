from schema.application import apiApplicationResource
from schema.tenant import Tenant


def test_tenant_defaults():
    t = Tenant(authority="https://login.microsoftonline.com/", client_id="abc", scope=["https://graph.microsoft.com/.default"])
    assert t.endpoint == "https://graph.microsoft.com/v1.0"
    assert t.connection == "app"
    assert t.access_token is None


def test_tenant_user_connection():
    t = Tenant(
        authority="https://login.microsoftonline.com/",
        client_id="abc",
        scope=["https://graph.microsoft.com/.default"],
        connection="user",
    )
    assert t.connection == "user"


def test_api_application_resource_defaults():
    r = apiApplicationResource()
    assert r.acceptMappedClaims is False
    assert r.requestedAccessTokenVersion == 1
    assert r.knownClientApplications == []
