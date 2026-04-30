import json
import os
import sys
from datetime import datetime
from typing import List, Optional
from src.core.redis_manager import RedisManager


class BackupService:
    @staticmethod
    def _get_base_dir():
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def __init__(self):
        base_dir = self._get_base_dir()
        self.backup_dir = os.path.join(base_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, redis_manager: RedisManager, pattern: str = "*") -> Optional[str]:
        if not redis_manager.is_connected:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"redis_backup_{timestamp}.json"
        filepath = os.path.join(self.backup_dir, filename)

        data = {
            "timestamp": timestamp,
            "server": f"{redis_manager.config.host}:{redis_manager.config.port}",
            "db": redis_manager.config.db,
            "keys": []
        }

        cursor = 0
        while True:
            cursor, batch = redis_manager._client.scan(cursor=cursor, match=pattern, count=1000)
            for key in batch:
                key_type = redis_manager._client.type(key)
                ttl = redis_manager._client.ttl(key)

                key_data = {
                    "key": key,
                    "type": key_type,
                    "ttl": ttl,
                    "value": None
                }

                if key_type == "string":
                    key_data["value"] = redis_manager._client.get(key)
                elif key_type == "hash":
                    key_data["value"] = redis_manager._client.hgetall(key)
                elif key_type == "list":
                    key_data["value"] = redis_manager._client.lrange(key, 0, -1)
                elif key_type == "set":
                    key_data["value"] = list(redis_manager._client.smembers(key))
                elif key_type == "zset":
                    key_data["value"] = redis_manager._client.zrange(key, 0, -1, withscores=True)

                data["keys"].append(key_data)

            if cursor == 0:
                break

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def restore_backup(self, redis_manager: RedisManager, filepath: str, overwrite: bool = False) -> tuple[bool, int]:
        if not os.path.exists(filepath):
            return False, 0

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        restored = 0
        for key_data in data.get("keys", []):
            key = key_data["key"]
            key_type = key_data["type"]
            value = key_data["value"]
            ttl = key_data.get("ttl", -1)

            if overwrite or not redis_manager._client.exists(key):
                if key_type == "string":
                    redis_manager._client.set(key, value)
                elif key_type == "hash":
                    redis_manager._client.hset(key, mapping=value)
                elif key_type == "list":
                    redis_manager._client.rpush(key, *value)
                elif key_type == "set":
                    redis_manager._client.sadd(key, *value)
                elif key_type == "zset":
                    redis_manager._client.zadd(key, {m: s for m, s in value})

                if ttl > 0:
                    redis_manager._client.expire(key, ttl)

                restored += 1

        return True, restored

    def list_backups(self) -> List[dict]:
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def delete_backup(self, filename: str) -> bool:
        filepath = os.path.join(self.backup_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
