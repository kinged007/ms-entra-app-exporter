from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Tenant(BaseModel):
    # name: str = Field(..., description="The name of the tenant")
    authority: str = Field(..., description="The authority of the tenant")
    client_id: str = Field(..., description="The client ID of the tenant")
    scope: List[str] = Field(["https://graph.microsoft.com/.default"], description="The scope of the tenant")
    connection: Literal['app', 'user'] = Field('app', description="The connection type of the tenant")
    private_key: Optional[str] = Field(None, description="The file path of the private certificate. Python requires a 'private_key' in PEM format")
    thumbprint: Optional[str] = Field(None, description="The thumbprint of the certificate")
    secret: Optional[str] = Field(None, description="The secret of the tenant")
    endpoint: str = Field("https://graph.microsoft.com/v1.0", description="The base URL of the tenant")
    # created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="The creation time of the tenant")
    file: Optional[str] = Field(None, description="The name of the tenant")
    access_token: Optional[str] = Field(None, description="The access token of the tenant. Never saved to file.")
