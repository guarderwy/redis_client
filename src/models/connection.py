from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ConnectionConfig:
    id: str
    name: str
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    username: Optional[str] = None
    separator: str = ":"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "password": self.password,
            "db": self.db,
            "ssl": self.ssl,
            "ssl_certfile": self.ssl_certfile,
            "ssl_keyfile": self.ssl_keyfile,
            "ssl_ca_certs": self.ssl_ca_certs,
            "username": self.username,
            "separator": self.separator,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectionConfig":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            host=data.get("host", "localhost"),
            port=int(data.get("port", 6379)),
            password=data.get("password"),
            db=int(data.get("db", 0)),
            ssl=bool(data.get("ssl", False)),
            ssl_certfile=data.get("ssl_certfile"),
            ssl_keyfile=data.get("ssl_keyfile"),
            ssl_ca_certs=data.get("ssl_ca_certs"),
            username=data.get("username"),
            separator=data.get("separator", ":"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

    def get_connection_kwargs(self) -> dict:
        kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "decode_responses": True,
        }
        if self.password:
            kwargs["password"] = self.password
        if self.username:
            kwargs["username"] = self.username
        if self.ssl:
            kwargs["ssl"] = True
            if self.ssl_certfile:
                kwargs["ssl_certfile"] = self.ssl_certfile
            if self.ssl_keyfile:
                kwargs["ssl_keyfile"] = self.ssl_keyfile
            if self.ssl_ca_certs:
                kwargs["ssl_ca_certs"] = self.ssl_ca_certs
        return kwargs
