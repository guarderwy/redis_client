import json
import csv
import os
from typing import List, Optional
from src.core.redis_manager import RedisManager


class ImportExportService:
    @staticmethod
    def export_to_json(redis_manager: RedisManager, filepath: str, pattern: str = "*") -> bool:
        if not redis_manager.is_connected:
            return False

        data = []
        cursor = 0
        while True:
            cursor, batch = redis_manager._client.scan(cursor=cursor, match=pattern, count=1000)
            for key in batch:
                key_type = redis_manager._client.type(key)
                ttl = redis_manager._client.ttl(key)
                value = redis_manager.get_key_value(key)

                data.append({
                    "key": key,
                    "type": key_type,
                    "ttl": ttl,
                    "value": value.value if value else None
                })
            if cursor == 0:
                break

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    @staticmethod
    def export_to_csv(redis_manager: RedisManager, filepath: str, pattern: str = "*") -> bool:
        if not redis_manager.is_connected:
            return False

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Key", "Type", "TTL", "Value"])

            cursor = 0
            while True:
                cursor, batch = redis_manager._client.scan(cursor=cursor, match=pattern, count=1000)
                for key in batch:
                    key_type = redis_manager._client.type(key)
                    ttl = redis_manager._client.ttl(key)
                    value = redis_manager.get_key_value(key)

                    value_str = str(value.value) if value else ""
                    writer.writerow([key, key_type, ttl, value_str])
                if cursor == 0:
                    break

        return True

    @staticmethod
    def import_from_json(redis_manager: RedisManager, filepath: str, overwrite: bool = False) -> tuple[bool, int]:
        if not os.path.exists(filepath):
            return False, 0

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported = 0
        for item in data:
            key = item.get("key")
            key_type = item.get("type")
            value = item.get("value")
            ttl = item.get("ttl", -1)

            if not key or not key_type:
                continue

            if overwrite or not redis_manager._client.exists(key):
                if redis_manager.set_key_value(key, key_type, value):
                    if ttl > 0:
                        redis_manager.set_ttl(key, ttl)
                    imported += 1

        return True, imported

    @staticmethod
    def import_from_csv(redis_manager: RedisManager, filepath: str, overwrite: bool = False) -> tuple[bool, int]:
        if not os.path.exists(filepath):
            return False, 0

        imported = 0
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("Key")
                key_type = row.get("Type", "string")
                value = row.get("Value", "")
                ttl = int(row.get("TTL", -1))

                if not key:
                    continue

                if overwrite or not redis_manager._client.exists(key):
                    if redis_manager.set_key_value(key, key_type, value):
                        if ttl > 0:
                            redis_manager.set_ttl(key, ttl)
                        imported += 1

        return True, imported
