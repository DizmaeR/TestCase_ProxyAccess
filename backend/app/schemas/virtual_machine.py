from pydantic import BaseModel, ConfigDict


class VirtualMachineResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    protocol: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ConnectionStatus(BaseModel):
    status: str
    vm_host: str | None = None
    vm_port: int | None = None
    vm_protocol: str | None = None
