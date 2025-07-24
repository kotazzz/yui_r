import json
import threading
import os
from typing import Callable, TypeVar, Optional, Any

T = TypeVar('T')

def identity(x):
    return x

def _get_nested(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    for key in keys[:-1]:
        data = data.get(key, {})
    return data.get(keys[-1], default)

def _set_nested(data: dict[str, Any], keys: list[str], value: Any) -> None:
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value

class SettingsStore:
    _instance = None
    _lock = threading.Lock()
    _file_path = "settings.json"

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SettingsStore, cls).__new__(cls)
                    cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        if os.path.exists(self._file_path):
            with open(self._file_path, "r", encoding="utf-8") as f:
                self._data: dict[str, Any] = json.load(f)
        else:
            self._data: dict[str, Any] = {}

    def _save(self) -> None:
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get[T](self, key: str, default: Optional[T] = None, type_: Optional[Callable[[Any], T]] = identity) -> Optional[T]:
        keys = key.split(".")
        value = _get_nested(self._data, keys, default)
        if type_ is not None and value is not None:
            try:
                return type_(value)
            except (ValueError, TypeError):
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        _set_nested(self._data, keys, value)
        self._save()

_settings = SettingsStore()

def get_settings() -> SettingsStore:
    return _settings

# Пример использования:
# store = get_settings()
# store.set("user.profile.age", "23")
# print(store.get("user.profile.age", type=int))  # 23