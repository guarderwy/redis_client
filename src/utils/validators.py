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
            if not isinstance(value, dict):
                return False, "Hash value must be a dictionary"
            return True, "Valid"

        elif key_type == "list":
            if not isinstance(value, list):
                return False, "List value must be a list"
            return True, "Valid"

        elif key_type == "set":
            if not isinstance(value, (list, set)):
                return False, "Set value must be a list or set"
            return True, "Valid"

        elif key_type == "zset":
            if not isinstance(value, list):
                return False, "Sorted set value must be a list of (member, score) tuples"
            for item in value:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    return False, "Each item must be a (member, score) tuple"
                try:
                    float(item[1])
                except (ValueError, TypeError):
                    return False, "Score must be a number"
            return True, "Valid"

        return False, f"Unknown key type: {key_type}"
