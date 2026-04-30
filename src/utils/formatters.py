import json
import xml.dom.minidom
from typing import Any


class DataFormatter:
    @staticmethod
    def format_json(data: str) -> str:
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return data

    @staticmethod
    def format_xml(data: str) -> str:
        try:
            parsed = xml.dom.minidom.parseString(data)
            return parsed.toprettyxml(indent="  ")
        except:
            return data

    @staticmethod
    def detect_format(data: str) -> str:
        data = data.strip()
        if not data:
            return "text"

        if data.startswith("{") or data.startswith("["):
            try:
                json.loads(data)
                return "json"
            except:
                pass

        if data.startswith("<?xml") or data.startswith("<"):
            try:
                xml.dom.minidom.parseString(data)
                return "xml"
            except:
                pass

        return "text"

    @staticmethod
    def format_value(value: Any, key_type: str) -> str:
        if value is None:
            return "(nil)"

        if key_type == "string":
            str_value = str(value)
            fmt = DataFormatter.detect_format(str_value)
            if fmt == "json":
                return DataFormatter.format_json(str_value)
            elif fmt == "xml":
                return DataFormatter.format_xml(str_value)
            return str_value

        elif key_type == "hash":
            if isinstance(value, dict):
                return json.dumps(value, indent=2, ensure_ascii=False)
            return str(value)

        elif key_type == "list":
            if isinstance(value, list):
                return json.dumps(value, indent=2, ensure_ascii=False)
            return str(value)

        elif key_type == "set":
            if isinstance(value, set):
                return json.dumps(sorted(list(value)), indent=2, ensure_ascii=False)
            return str(value)

        elif key_type == "zset":
            if isinstance(value, list):
                mapping = {}
                for member, score in value:
                    mapping[member] = score
                return json.dumps(mapping, indent=2, ensure_ascii=False)
            return str(value)

        return str(value)

    @staticmethod
    def format_bytes(num_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.2f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.2f} PB"

    @staticmethod
    def format_ttl(ttl: int) -> str:
        if ttl == -1:
            return "No expiry"
        if ttl == -2:
            return "Expired"
        if ttl < 60:
            return f"{ttl}s"
        if ttl < 3600:
            minutes = ttl // 60
            seconds = ttl % 60
            return f"{minutes}m {seconds}s"
        if ttl < 86400:
            hours = ttl // 3600
            minutes = (ttl % 3600) // 60
            return f"{hours}h {minutes}m"
        days = ttl // 86400
        hours = (ttl % 86400) // 3600
        return f"{days}d {hours}h"

    @staticmethod
    def parse_value_for_save(value: str, key_type: str) -> Any:
        if key_type == "string":
            return value

        elif key_type == "hash":
            data = json.loads(value)
            if not isinstance(data, dict):
                raise ValueError("Hash value must be JSON object format")
            return {k: str(v) for k, v in data.items()}

        elif key_type == "list":
            data = json.loads(value)
            if not isinstance(data, list):
                raise ValueError("List value must be JSON array format")
            return [str(item) for item in data]

        elif key_type == "set":
            data = json.loads(value)
            if not isinstance(data, list):
                raise ValueError("Set value must be JSON array format")
            return set(str(item) for item in data)

        elif key_type == "zset":
            data = json.loads(value)
            if not isinstance(data, dict):
                raise ValueError("Zset value must be JSON object format")
            return {k: float(v) for k, v in data.items()}

        return value
