import json
import os
from typing import List, Optional
from src.models.connection import ConnectionConfig


class ConfigManager:
    CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "connections.json")

    def __init__(self):
        os.makedirs(self.CONFIG_DIR, exist_ok=True)
        self._connections: List[ConnectionConfig] = []
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._connections = [ConnectionConfig.from_dict(d) for d in data.get("connections", [])]
            except (json.JSONDecodeError, KeyError):
                self._connections = []

    def _save_config(self):
        data = {
            "connections": [c.to_dict() for c in self._connections],
            "version": "1.0"
        }
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all_connections(self) -> List[ConnectionConfig]:
        return self._connections.copy()

    def get_connection(self, conn_id: str) -> Optional[ConnectionConfig]:
        for conn in self._connections:
            if conn.id == conn_id:
                return conn
        return None

    def add_connection(self, config: ConnectionConfig) -> ConnectionConfig:
        self._connections.append(config)
        self._save_config()
        return config

    def update_connection(self, config: ConnectionConfig) -> Optional[ConnectionConfig]:
        for i, conn in enumerate(self._connections):
            if conn.id == config.id:
                self._connections[i] = config
                self._save_config()
                return config
        return None

    def delete_connection(self, conn_id: str) -> bool:
        for i, conn in enumerate(self._connections):
            if conn.id == conn_id:
                self._connections.pop(i)
                self._save_config()
                return True
        return False

    def get_connection_by_name(self, name: str) -> Optional[ConnectionConfig]:
        for conn in self._connections:
            if conn.name == name:
                return conn
        return None
