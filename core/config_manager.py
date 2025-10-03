# core/config_manager.py
import os
from typing import Dict, List

class ConfigManager:
    def __init__(self, cfg_folder: str):
        self.cfg_folder = cfg_folder
        self.client_path = os.path.join(cfg_folder, "client.cfg")
        self.keys_path = os.path.join(cfg_folder, "keys.cfg")

        self.client_lines: List[str] = []
        self.keys_lines: List[str] = []

        self.client_data: Dict[str, str] = {}
        self.keys_data: Dict[str, str] = {}

        self._load_configs()

    # ---------------- LOAD ----------------
    def _load_configs(self):
        self.client_data = self._parse_client_file(self.client_path)
        self.keys_data = self._parse_keys_file(self.keys_path)

    def _parse_client_file(self, path: str) -> Dict[str, str]:
        data = {}
        self.client_lines = []
        if not os.path.exists(path):
            return data
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                self.client_lines = f.readlines()
            for line in self.client_lines:
                s = line.strip()
                if not s or s.startswith("//"):
                    continue
                parts = s.split(maxsplit=1)
                if len(parts) >= 2:
                    key = parts[0]
                    val = parts[1].split("//")[0].strip()  # отрезаем коммент
                    val = val.strip('"')                  # убираем кавычки
                    data[key] = val
        except Exception as e:
            print(f"Ошибка при чтении {path}: {e}")
        return data

    def _parse_keys_file(self, path: str) -> Dict[str, str]:
        data = {}
        self.keys_lines = []
        if not os.path.exists(path):
            return data
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                self.keys_lines = f.readlines()
            for line in self.keys_lines:
                s = line.strip()
                if not s or s.startswith("//"):
                    continue
                if s.lower().startswith("bind "):
                    parts = s.split(maxsplit=2)
                    if len(parts) >= 3:
                        key = parts[1]
                        val = parts[2].split("//")[0].strip().strip('"')
                        data[key] = val
        except Exception as e:
            print(f"Ошибка при чтении {path}: {e}")
        return data

    # ---------------- GET/SET ----------------
    def get_value(self, key: str, file_type: str = "client") -> str:
        if (file_type or "client").lower() == "client":
            return self.client_data.get(key, "")
        return self.keys_data.get(key, "")

    def set_value(self, key: str, value: str, file_type: str = "client"):
        ftype = (file_type or "client").lower()
        value = "" if value is None else str(value)

        print(f"[DEBUG] set_value: key={key}, value={value}, file_type={ftype}")

        if ftype == "client":
            self.client_data[key] = value
            self.client_lines = self._set_value_in_lines(
                self.client_lines, key, value, self._format_client_line
            )
        else:
            self.keys_data[key] = value
            self.keys_lines = self._set_value_in_lines(
                self.keys_lines, key, value, self._format_bind_line, is_bind=True
            )

    # ---------------- HELPERS ----------------
    def _set_value_in_lines(self, lines: list, key: str, value: str, formatter, is_bind=False) -> list:
        new_lines = []
        found = False
        for line in lines:
            s = line.strip()
            if not s or s.startswith("//"):
                new_lines.append(line)
                continue

            if is_bind:
                if s.lower().startswith("bind "):
                    parts = s.split(maxsplit=2)
                    if len(parts) >= 2 and parts[1] == key:
                        print(f"[DEBUG] Updating bind {key} → {value}")
                        comment = ""
                        if "//" in line:
                            comment = " //" + line.split("//", 1)[1].rstrip()
                        new_lines.append(formatter(key, value).rstrip("\n") + comment + "\n")
                        found = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                parts = s.split(maxsplit=1)
                if len(parts) >= 2 and parts[0] == key:
                    print(f"[DEBUG] Updating var {key}: {parts[1]} → {value}")
                    comment = ""
                    if "//" in line:
                        comment = " //" + line.split("//", 1)[1].rstrip()
                    new_lines.append(formatter(key, value).rstrip("\n") + comment + "\n")
                    found = True
                else:
                    new_lines.append(line)

        if not found:
            print(f"[DEBUG] Key {key} not found, adding new line")
            new_lines.append(formatter(key, value))
        return new_lines


    def _format_client_line(self, key: str, value: str) -> str:
        # Числа (целые и дробные) — без кавычекhb.ktyi
        if self._is_number(value):
            return f"{key} {value}\n"
        # Всё остальное — в кавычках, включая "True", "False", "on", "off" и т.д.
        return f'{key} "{value}"\n'

    def _format_bind_line(self, key: str, value: str) -> str:
        return f'bind {key} "{value}"\n'

    def _is_number(self, s: str) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False

    # ---------------- SAVE ----------------
    def save(self):
        try:
            with open(self.client_path, "w", encoding="utf-8") as f:
                f.writelines(self.client_lines)
        except Exception as e:
            print(f"Ошибка при записи {self.client_path}: {e}")

        try:
            with open(self.keys_path, "w", encoding="utf-8") as f:
                f.writelines(self.keys_lines)
        except Exception as e:
            print(f"Ошибка при записи {self.keys_path}: {e}")
