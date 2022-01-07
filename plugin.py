from LSP.plugin import AbstractPlugin
from LSP.plugin import MarkdownLangMap
from LSP.plugin import register_plugin
from LSP.plugin import unregister_plugin
from LSP.plugin.core.sessions import Session
from LSP.plugin.core.typing import Any, List, Dict, Optional, Tuple
import functools
import os
import shutil
import sublime
import tempfile
import urllib.request
import weakref
import zipfile

URL = "https://github.com/sumneko/vscode-lua/releases/download/v{v}/vscode-lua-v{v}-{platform_arch}.vsix"


class Lua(AbstractPlugin):
    @classmethod
    def name(cls) -> str:
        return "LSP-{}".format(cls.__name__.lower())

    @classmethod
    def basedir(cls) -> str:
        return os.path.join(cls.storage_path(), cls.name())

    @classmethod
    def version_file(cls) -> str:
        return os.path.join(cls.basedir(), "VERSION")

    @classmethod
    def platform_arch(cls) -> str:
        return {
            "linux_x64": "linux-x64",
            "osx_arm64": "darwin-arm64",
            "osx_x64": "darwin-x64",
            "windows_x32": "win32-ia32",
            "windows_x64": "win32-x64",
        }[sublime.platform() + "_" + sublime.arch()]

    @classmethod
    def needs_update_or_installation(cls) -> bool:
        settings, _ = cls.configuration()
        server_version = str(settings.get("server_version"))
        try:
            with open(cls.version_file(), "r") as fp:
                return server_version != fp.read().strip()
        except OSError:
            return True

    @classmethod
    def install_or_update(cls) -> None:
        shutil.rmtree(cls.basedir(), ignore_errors=True)
        try:
            settings, _ = cls.configuration()
            server_version = str(settings.get("server_version"))
            with tempfile.TemporaryDirectory() as tmp:
                # Download the VSIX file
                zip_file = os.path.join(tmp, "lua.vsix")
                urllib.request.urlretrieve(URL.format(v=server_version, platform_arch=cls.platform_arch()), zip_file)
                # VSIX files are just zipfiles
                with zipfile.ZipFile(zip_file, "r") as z:
                    z.extractall(tmp)
                for root, dirs, files in os.walk(os.path.join(tmp, "extension", "server", "bin")):
                    for file in files:
                        os.chmod(os.path.join(root, file), 0o744)
                # Make sure package storage path exists for new users
                os.makedirs(cls.storage_path(), exist_ok=True)
                # Move the relevant subdirectory to the package storage
                shutil.move(os.path.join(tmp, "extension", "server"), cls.basedir())
            # Write the version stamp
            with open(cls.version_file(), "w") as fp:
                fp.write(server_version)
        except Exception:
            shutil.rmtree(cls.basedir(), ignore_errors=True)
            raise

    @classmethod
    def configuration(cls) -> Tuple[sublime.Settings, str]:
        base_name = "{}.sublime-settings".format(cls.name())
        file_path = "Packages/{}/{}".format(cls.name(), base_name)
        return sublime.load_settings(base_name), file_path

    @classmethod
    def additional_variables(cls) -> Optional[Dict[str, str]]:
        settings, _ = cls.configuration()
        return {
            "platform_arch": cls.platform_arch(),
            "locale": str(settings.get("locale")),
            "3rd": os.path.join(cls.basedir(), "meta", "3rd")
        }

    @classmethod
    def markdown_language_id_to_st_syntax_map(cls) -> Optional[MarkdownLangMap]:
        return {"lua": (("lua",), ("LSP-lua/codeblocks",))}

    def __init__(self, weaksession: 'weakref.ref[Session]') -> None:
        super().__init__(weaksession)
        self._settings_change_count = 0
        self._queued_changes = []  # type: List[Dict[str, Any]]

    def m___command(self, params: Any) -> None:
        """Handles the $/command notification."""
        if not isinstance(params, dict):
            return print("{}: cannot handle command: expected dict, got {}".format(self.name(), type(params)))
        command = params["command"]
        if command == "lua.config":
            self._queued_changes.extend(params["data"])
            self._settings_change_count += 1
            current_count = self._settings_change_count
            sublime.set_timeout_async(functools.partial(self._handle_config_commands_async, current_count), 200)
        else:
            sublime.error_message("LSP-lua: unrecognized command: {}".format(command))

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
            sublime.message_dialog(" ".join((
                "The server settings have been applied in the Window,",
                "but this Window is not backed by a .sublime-project.",
                "Click on Project > Save Project As... to store the settings."
            )))

    def _get_server_settings(self, window: sublime.Window) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
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
    register_plugin(Lua)


def plugin_unloaded() -> None:
    unregister_plugin(Lua)
