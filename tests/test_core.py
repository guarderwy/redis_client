import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.connection import ConnectionConfig
from src.core.config_manager import ConfigManager
from src.utils.formatters import DataFormatter
from src.utils.validators import DataValidator


class TestConnectionConfig(unittest.TestCase):
    def test_create_connection(self):
        config = ConnectionConfig(
            id="test-1",
            name="Test Server",
            host="localhost",
            port=6379
        )
        self.assertEqual(config.name, "Test Server")
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 6379)

    def test_connection_to_dict(self):
        config = ConnectionConfig(
            id="test-1",
            name="Test Server"
        )
        data = config.to_dict()
        self.assertIn("name", data)
        self.assertEqual(data["name"], "Test Server")

    def test_connection_from_dict(self):
        data = {
            "id": "test-1",
            "name": "Test Server",
            "host": "127.0.0.1",
            "port": 6380
        }
        config = ConnectionConfig.from_dict(data)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 6380)


class TestDataFormatter(unittest.TestCase):
    def test_format_json(self):
        input_data = '{"name": "test", "value": 123}'
        formatted = DataFormatter.format_json(input_data)
        self.assertIn("\n", formatted)

    def test_detect_json(self):
        self.assertEqual(DataFormatter.detect_format('{"key": "value"}'), "json")

    def test_detect_text(self):
        self.assertEqual(DataFormatter.detect_format("plain text"), "text")

    def test_format_ttl(self):
        self.assertEqual(DataFormatter.format_ttl(-1), "No expiry")
        self.assertEqual(DataFormatter.format_ttl(30), "30s")
        self.assertIn("m", DataFormatter.format_ttl(120))


class TestDataValidator(unittest.TestCase):
    def test_valid_json(self):
        valid, msg = DataValidator.validate_json('{"key": "value"}')
        self.assertTrue(valid)

    def test_invalid_json(self):
        valid, msg = DataValidator.validate_json('{invalid}')
        self.assertFalse(valid)

    def test_validate_string(self):
        valid, msg = DataValidator.validate_value("test", "string")
        self.assertTrue(valid)

    def test_validate_hash(self):
        valid, msg = DataValidator.validate_value({"field": "value"}, "hash")
        self.assertTrue(valid)

    def test_validate_list(self):
        valid, msg = DataValidator.validate_value(["item1", "item2"], "list")
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
