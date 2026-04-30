import time
from typing import List, Optional, Any, Dict, Tuple
import redis
from src.models.connection import ConnectionConfig
from src.models.key_data import KeyInfo, KeyValue


class RedisManager:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._config: Optional[ConnectionConfig] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    @property
    def client(self) -> Optional[redis.Redis]:
        return self._client

    @property
    def config(self) -> Optional[ConnectionConfig]:
        return self._config

    def connect(self, config: ConnectionConfig) -> Tuple[bool, str]:
        try:
            self._client = redis.Redis(**config.get_connection_kwargs())
            self._client.ping()
            self._config = config
            self._connected = True
            return True, "Connected successfully"
        except redis.ConnectionError as e:
            return False, f"Connection failed: {str(e)}"
        except redis.AuthenticationError as e:
            return False, f"Authentication failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def disconnect(self):
        if self._client:
            try:
                self._client.close()
            except:
                pass
        self._client = None
        self._config = None
        self._connected = False

    def test_connection(self, config: ConnectionConfig) -> Tuple[bool, str]:
        try:
            client = redis.Redis(**config.get_connection_kwargs())
            client.ping()
            client.close()
            return True, "Connection successful"
        except redis.ConnectionError as e:
            return False, f"Connection failed: {str(e)}"
        except redis.AuthenticationError as e:
            return False, f"Authentication failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_keys(self, pattern: str = "*", page: int = 0, page_size: int = 100, key_type: str = None) -> List[KeyInfo]:
        if not self.is_connected:
            return []

        keys = []
        cursor = 0
        count = 0
        start = page * page_size
        end = start + page_size

        while True:
            cursor, batch = self._client.scan(cursor=cursor, match=pattern, count=min(page_size * 2, 1000))
            for key in batch:
                key_type_actual = self._client.type(key)
                if key_type and key_type_actual != key_type:
                    count += 1
                    continue
                if start <= count < end:
                    ttl = self._client.ttl(key)
                    keys.append(KeyInfo(key=key, key_type=key_type_actual, ttl=ttl))
                count += 1
                if count >= end and cursor == 0:
                    return keys
            if cursor == 0:
                break

        return keys

    def get_key_count(self, pattern: str = "*", key_type: str = None) -> int:
        if not self.is_connected:
            return 0

        count = 0
        cursor = 0
        while True:
            cursor, batch = self._client.scan(cursor=cursor, match=pattern, count=1000)
            for key in batch:
                if key_type:
                    if self._client.type(key) == key_type:
                        count += 1
                else:
                    count += 1
            if cursor == 0:
                break
        return count

    def get_key_value(self, key: str) -> Optional[KeyValue]:
        if not self.is_connected:
            return None

        key_type = self._client.type(key)
        ttl = self._client.ttl(key)

        if key_type == "string":
            value = self._client.get(key)
        elif key_type == "hash":
            value = self._client.hgetall(key)
        elif key_type == "list":
            value = self._client.lrange(key, 0, -1)
        elif key_type == "set":
            value = self._client.smembers(key)
        elif key_type == "zset":
            value = self._client.zrange(key, 0, -1, withscores=True)
        else:
            value = None

        return KeyValue(key=key, key_type=key_type, value=value, ttl=ttl)

    def set_key_value(self, key: str, key_type: str, value: Any, ttl: int = -1) -> bool:
        if not self.is_connected:
            return False

        try:
            if key_type == "string":
                self._client.set(key, value)
            elif key_type == "hash":
                self._client.delete(key)
                if isinstance(value, dict):
                    self._client.hset(key, mapping={k: str(v) for k, v in value.items()})
            elif key_type == "list":
                self._client.delete(key)
                if isinstance(value, list):
                    self._client.rpush(key, *[str(v) for v in value])
            elif key_type == "set":
                self._client.delete(key)
                if isinstance(value, (list, set)):
                    self._client.sadd(key, *[str(v) for v in value])
            elif key_type == "zset":
                self._client.delete(key)
                if isinstance(value, dict):
                    self._client.zadd(key, {k: float(v) for k, v in value.items()})

            if ttl > 0:
                self._client.expire(key, ttl)

            return True
        except Exception:
            return False

    def delete_key(self, key: str) -> bool:
        if not self.is_connected:
            return False
        try:
            return self._client.delete(key) > 0
        except:
            return False

    def delete_keys(self, keys: List[str]) -> int:
        if not self.is_connected:
            return 0
        try:
            return self._client.delete(*keys)
        except:
            return 0

    def set_ttl(self, key: str, ttl: int) -> bool:
        if not self.is_connected:
            return False
        if ttl == -1:
            return self._client.persist(key)
        return self._client.expire(key, ttl)

    def rename_key(self, old_key: str, new_key: str) -> bool:
        if not self.is_connected:
            return False
        try:
            self._client.rename(old_key, new_key)
            return True
        except:
            return False

    def execute_command(self, command: str) -> Tuple[Any, float, bool]:
        if not self.is_connected:
            return "Not connected", 0, False

        start_time = time.time()
        try:
            parts = command.strip().split()
            if not parts:
                return "Empty command", 0, False

            cmd = parts[0].upper()
            args = parts[1:]

            result = self._client.execute_command(cmd, *args)
            duration = (time.time() - start_time) * 1000
            return result, duration, True
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return str(e), duration, False

    def get_server_info(self) -> Dict[str, Any]:
        if not self.is_connected:
            return {}

        info = self._client.info()
        return {
            "redis_version": info.get("redis_version", "Unknown"),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
            "used_memory_rss_human": info.get("used_memory_rss_human", "0B"),
            "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
            "total_connections_received": info.get("total_connections_received", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "db_size": self._client.dbsize(),
            "evicted_keys": info.get("evicted_keys", 0),
            "expired_keys": info.get("expired_keys", 0),
        }

    def get_databases(self) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []

        info = self._client.info()
        dbs = []
        for key, value in info.items():
            if key.startswith("db"):
                parts = key.split(",")
                if len(parts) == 3:
                    db_name = key
                    keys = int(parts[0].split("=")[1]) if "=" in parts[0] else 0
                    expires = int(parts[1].split("=")[1]) if "=" in parts[1] else 0
                    avg_ttl = int(parts[2].split("=")[1]) if "=" in parts[2] else 0
                    dbs.append({
                        "name": db_name,
                        "keys": keys,
                        "expires": expires,
                        "avg_ttl": avg_ttl,
                    })
        return dbs

    def flush_db(self) -> bool:
        if not self.is_connected:
            return False
        try:
            self._client.flushdb()
            return True
        except:
            return False

    def get_key_types(self) -> Dict[str, int]:
        if not self.is_connected:
            return {}

        types_count = {"string": 0, "hash": 0, "list": 0, "set": 0, "zset": 0, "other": 0}
        cursor = 0
        while True:
            cursor, batch = self._client.scan(cursor=cursor, count=1000)
            for key in batch:
                key_type = self._client.type(key)
                if key_type in types_count:
                    types_count[key_type] += 1
                else:
                    types_count["other"] += 1
            if cursor == 0:
                break
        return types_count
