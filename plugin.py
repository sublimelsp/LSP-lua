from __future__ import annotations

from LSP.plugin import ClientConfig
from LSP.plugin import LspPlugin
from LSP.plugin import notification_handler
from LSP.plugin import OnPreStartContext
from LSP.plugin import Session
from typing import Any
import functools
import os
import shutil
import sublime
import tarfile
import tempfile
import urllib.request
import weakref
import zipfile

URL = "https://github.com/LuaLS/lua-language-server/releases/download/{v}/lua-language-server-{v}-{platform_arch}"

class Lua(LspPlugin):
    @classmethod
    def on_pre_start_async(cls, context: OnPreStartContext) -> None:
        configuration = context.configuration
        server_version = str(configuration.root_settings.get("server_version"))
        if cls.needs_update_or_installation(server_version):
            cls.install_or_update(server_version)
        context.variables.update(cls.additional_variables(configuration))

    @classmethod
    def basedir(cls) -> str:
        return str(cls.plugin_storage_path)

    @classmethod
    def version_file(cls) -> str:
        return os.path.join(cls.basedir(), "VERSION")

    @classmethod
    def platform_arch(cls) -> str:
        return {
            "linux_x64": "linux-x64.tar.gz",
            "osx_arm64": "darwin-arm64.tar.gz",
            "osx_x64": "darwin-x64.tar.gz",
            "windows_x32": "win32-ia32.zip",
            "windows_x64": "win32-x64.zip",
        }[sublime.platform() + "_" + sublime.arch()]

    @classmethod
    def needs_update_or_installation(cls, server_version: str) -> bool:
        try:
            with open(cls.version_file(), "r") as fp:
                return server_version != fp.read().strip()
        except OSError:
            return True

    @classmethod
    def install_or_update(cls, server_version: str) -> None:
        shutil.rmtree(cls.basedir(), ignore_errors=True)
        try:
            with tempfile.TemporaryDirectory() as tempdir:
                downloaded_file = os.path.join(tempdir, "lua-lang-download")
                platform = cls.platform_arch()
                urllib.request.urlretrieve(URL.format(v=server_version, platform_arch=cls.platform_arch()), downloaded_file)
                if platform == "win32-ia32.zip" or platform == "win32-x64.zip":
                    with zipfile.ZipFile(downloaded_file, "r") as z:
                        z.extractall(tempdir)
                else:
                    with tarfile.open(downloaded_file) as z:
                        z.extractall(tempdir)
                os.makedirs(os.path.dirname(cls.basedir()), exist_ok=True)
                shutil.move(tempdir, cls.basedir())
            with open(cls.version_file(), "w") as fp:
                fp.write(server_version)
            shutil.rmtree(os.path.join(tempdir), ignore_errors=True)
        except Exception:
            shutil.rmtree(cls.basedir(), ignore_errors=True)
            raise

    @classmethod
    def additional_variables(cls, configuration: ClientConfig) -> dict[str, str]:
        locale = str(configuration.root_settings.get("locale"))
        return {
            "platform_arch": cls.platform_arch(),
            "locale": locale,
            "language": locale,
            "version": str(configuration.settings.get("Lua.runtime.version") or "Lua 5.4"),
            "encoding": str(configuration.settings.get("Lua.runtime.fileEncoding") or "utf8"),
            "3rd": os.path.join(cls.basedir(), "meta", "3rd")
        }

    def __init__(self, weaksession: weakref.ref[Session]) -> None:
        super().__init__(weaksession)
        self._settings_change_count = 0
        self._queued_changes: list[dict[str, Any]] = []

    @notification_handler("$/command")
    def on_command(self, params: Any) -> None:
        if not isinstance(params, dict):
            return print(f"{self.name}: cannot handle command: expected dict, got {type(params)}")
        command = params["command"]
        if command == "lua.config":
            self._queued_changes.extend(params["data"])
            self._settings_change_count += 1
            current_count = self._settings_change_count
            sublime.set_timeout_async(functools.partial(self._handle_config_commands_async, current_count), 200)
        else:
            sublime.error_message(f"LSP-lua: unrecognized command: {command}")

    def _handle_config_commands_async(self, settings_change_count: int) -> None:
        if self._settings_change_count != settings_change_count:
            return
        commands, self._queued_changes = self._queued_changes, []
        session = self.weaksession()
        if not session:
            return
        base, settings = self._get_server_settings(session.window)
        if base is None or settings is None:
            return
        for command in commands:
            action = command["action"]
            key = command["key"]
            value = command["value"]
            if action == "set":
                settings[key] = value
            elif action == "add":
                values = settings.get(key)
                if not isinstance(values, list):
                    values = []
                values.append(value)
                settings[key] = values
            else:
                print("LSP-lua: unrecognized action:", action)
        session.window.set_project_data(base)
        if not session.window.project_file_name():
            sublime.message_dialog((  # noqa: UP034
                "The server settings have been applied in the Window, "
                "but this Window is not backed by a .sublime-project. "
                "Click on Project > Save Project As... to store the settings."
            ))

    def _get_server_settings(self, window: sublime.Window) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        data = window.project_data()
        if not isinstance(data, dict):
            return None, None
        if "settings" not in data:
            data["settings"] = {}
        if "LSP" not in data["settings"]:
            data["settings"]["LSP"] = {}
        if "LSP-lua" not in data["settings"]["LSP"]:
            data["settings"]["LSP"]["LSP-lua"] = {}
        if "settings" not in data["settings"]["LSP"]["LSP-lua"]:
            data["settings"]["LSP"]["LSP-lua"]["settings"] = {}
        return data, data["settings"]["LSP"]["LSP-lua"]["settings"]


def plugin_loaded() -> None:
    Lua.register()


def plugin_unloaded() -> None:
    Lua.unregister()
