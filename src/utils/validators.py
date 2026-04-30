import json
from typing import Any


class DataValidator:
    @staticmethod
    def validate_json(data: str) -> tuple[bool, str]:
        try:
            json.loads(data)
            return True, "Valid JSON"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"

    @staticmethod
    def validate_xml(data: str) -> tuple[bool, str]:
        import xml.dom.minidom
        try:
            xml.dom.minidom.parseString(data)
            return True, "Valid XML"
        except Exception as e:
            return False, f"Invalid XML: {str(e)}"

    @staticmethod
    def validate_value(value: Any, key_type: str) -> tuple[bool, str]:
        if key_type == "string":
            return True, "Valid"

        elif key_type == "hash":
            try:
                data = json.loads(value) if isinstance(value, str) else value
                if not isinstance(data, dict):
                    return False, "Hash value must be JSON object format"
                return True, "Valid"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON format: {str(e)}"

        elif key_type == "list":
            try:
                data = json.loads(value) if isinstance(value, str) else value
                if not isinstance(data, list):
                    return False, "List value must be JSON array format"
                return True, "Valid"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON format: {str(e)}"

        elif key_type == "set":
            try:
                data = json.loads(value) if isinstance(value, str) else value
                if not isinstance(data, list):
                    return False, "Set value must be JSON array format"
                return True, "Valid"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON format: {str(e)}"

        elif key_type == "zset":
            try:
                data = json.loads(value) if isinstance(value, str) else value
                if not isinstance(data, dict):
                    return False, "Zset value must be JSON object format (member: score)"
                for member, score in data.items():
                    try:
                        float(score)
                    except (ValueError, TypeError):
                        return False, f"Score for member '{member}' must be a number"
                return True, "Valid"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON format: {str(e)}"

        return False, f"Unknown key type: {key_type}"
