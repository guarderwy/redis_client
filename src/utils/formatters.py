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
            if isinstance(value, (set, list)):
                return json.dumps(sorted(value, key=str), indent=2, ensure_ascii=False)
            return str(value)

        elif key_type == "zset":
            if isinstance(value, dict):
                return json.dumps(value, indent=2, ensure_ascii=False)
            if isinstance(value, list):
                result = {}
                for member, score in value:
                    result[member] = score
                return json.dumps(result, indent=2, ensure_ascii=False)
            return str(value)

        return str(value)

    @staticmethod
    def parse_value_for_save(value: str, key_type: str) -> Any:
        """解析编辑后的值，转换为可保存的格式"""
        if key_type == "string":
            return value

        elif key_type == "hash":
            return json.loads(value)

        elif key_type == "list":
            return json.loads(value)

        elif key_type == "set":
            return json.loads(value)

        elif key_type == "zset":
            data = json.loads(value)
            return {k: float(v) for k, v in data.items()}

        return value

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
            return "永不过期"
        if ttl == -2:
            return "已过期"
        if ttl < 60:
            return f"{ttl}秒"
        if ttl < 3600:
            minutes = ttl // 60
            seconds = ttl % 60
            return f"{minutes}分 {seconds}秒"
        if ttl < 86400:
            hours = ttl // 3600
            minutes = (ttl % 3600) // 60
            return f"{hours}小时 {minutes}分"
        days = ttl // 86400
        hours = (ttl % 86400) // 3600
        return f"{days}天 {hours}小时"
