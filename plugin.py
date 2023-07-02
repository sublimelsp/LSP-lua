from LSP.plugin import AbstractPlugin
from LSP.plugin import register_plugin
from LSP.plugin import unregister_plugin
from LSP.plugin.core.sessions import Session
from LSP.plugin.core.typing import Any, Dict, List, Optional, Tuple  # noqa: F401
from distutils.dir_util import copy_tree
import os
import shutil
from LSP.plugin.core.views import KIND_PACKAGE
import sublime
import tempfile
import urllib.request
import weakref
import zipfile
import tarfile
import sublime_plugin
import json

URL = "https://github.com/sumneko/lua-language-server/releases/download/{v}/lua-language-server-{v}-{platform_arch}"


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
            "linux_x64": "linux-x64.tar.gz",
            "osx_arm64": "darwin-arm64.tar.gz",
            "osx_x64": "darwin-x64.tar.gz",
            "windows_x32": "win32-ia32.zip",
            "windows_x64": "win32-x64.zip",
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
                downloaded_file = os.path.join(tmp, "lua-lang-download")
                platform = cls.platform_arch()
                urllib.request.urlretrieve(
                    URL.format(v=server_version, platform_arch=cls.platform_arch()),
                    downloaded_file,
                )
                if platform == "win32-ia32.zip" or platform == "win32-x64.zip":
                    with zipfile.ZipFile(downloaded_file, "r") as z:
                        z.extractall(tmp)
                else:
                    with tarfile.open(downloaded_file) as z:
                        z.extractall(tmp)
                os.makedirs(cls.storage_path(), exist_ok=True)
                copy_tree(os.path.join(tmp), cls.basedir())
            with open(cls.version_file(), "w") as fp:
                fp.write(server_version)
            shutil.rmtree(os.path.join(tmp), ignore_errors=True)
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
            "language": str(settings.get("locale")),
            "version": str(
                settings.get("settings").get("Lua.runtime.version") or "Lua 5.4"
            ),
            "encoding": str(
                settings.get("settings").get("Lua.runtime.fileEncoding") or "utf8"
            ),
            "3rd": os.path.join(cls.basedir(), "meta", "3rd"),
        }

    def __init__(self, weaksession: "weakref.ref[Session]") -> None:
        super().__init__(weaksession)
        self._settings_change_count = 0
        self._queued_changes = []  # type: List[Dict[str, Any]]

    def m___command(self, params: Any) -> None:
        """Handles the $/command notification."""
        if not isinstance(params, dict):
            return print(
                "{}: cannot handle command: expected dict, got {}".format(
                    self.name(), type(params)
                )
            )
        command = params["command"]
        if command == "lua.config":
            session = self.weaksession()
            if not session:
                print("no session to configure settings")
                return
            sublime.set_timeout(
                lambda: self._handle_config_commands(session.window, params["data"])
            )
        else:
            sublime.error_message("LSP-lua: unrecognized command: {}".format(command))

    def _handle_config_commands(
        self, window: sublime.Window, commands: List[Dict[str, Any]]
    ) -> None:
        print("_handle_config_commands", commands)
        base, settings = self.get_server_settings(window)
        if base is None or settings is None:
            "base is None or settings is None"
            return
        for command in commands:
            print("handling command", command)
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
        _update_project_data(window, base)

    @classmethod
    def get_server_settings(
        cls, window: sublime.Window
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
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


def _update_project_data(window: sublime.Window, data: Dict[str, Any]) -> None:
    window.set_project_data(data)
    if not window.project_file_name():
        sublime.message_dialog(
            " ".join(
                (
                    "The server settings have been applied in the Window,",
                    "but this Window is not backed by a .sublime-project.",
                    "Click on Project > Save Project As... to store the settings.",
                )
            )
        )
    else:
        sublime.message_dialog(
            "Your project settings, located at "
            + window.project_file_name()
            + ", have been updated with additional settings"
        )


def _load_3rdparty_config(folder: str) -> Any:
    with open(
        os.path.join(Lua.basedir(), "meta", "3rd", folder, "config.json"), "r"
    ) as fp:
        return json.load(fp)


class LspLuaSetupEnvironmentCommand(sublime_plugin.WindowCommand):
    def input(self, args: Any) -> Optional[sublime_plugin.CommandInputHandler]:
        if "environment" not in args:

            class EnvironmentInputHandler(sublime_plugin.ListInputHandler):
                def list_items(self) -> List[sublime.ListInputItem]:
                    result = []  # type: List[sublime.ListInputItem]
                    for folder in os.listdir(
                        os.path.join(Lua.basedir(), "meta", "3rd")
                    ):
                        self._list_item(folder, result)
                    return result

                def _list_item(
                    self, folder: str, result: List[sublime.ListInputItem]
                ) -> None:
                    if folder == "example":
                        return
                    directory = os.path.join(Lua.basedir(), "meta", "3rd", folder)
                    if not os.path.isdir(directory) or not os.path.isfile(
                        os.path.join(directory, "config.json")
                    ):
                        return
                    try:
                        config = _load_3rdparty_config(folder)
                        if not isinstance(config, dict):
                            return
                        name = config.pop("name", None)
                        if not isinstance(name, str):
                            name = folder
                        if isinstance(name, str):
                            result.append(
                                sublime.ListInputItem(
                                    text=name,
                                    value=folder,
                                    annotation=directory,
                                    kind=KIND_PACKAGE,
                                )
                            )
                    except Exception as ex:
                        print("failed parse config for", directory, ex)

            return EnvironmentInputHandler()

        return None

    def run(self, environment: str) -> None:
        data, settings = Lua.get_server_settings(self.window)
        if not isinstance(data, dict) or not isinstance(settings, dict):
            return
        config = _load_3rdparty_config(environment)
        if not isinstance(config, dict):
            return
        env_settings = config.pop("settings", None)
        if isinstance(env_settings, dict):
            settings.update(env_settings)
        libraries = set(settings.get("Lua.workspace.library", []))
        libraries.add("${3rd}/" + environment + "/library")
        settings["Lua.workspace.library"] = list(libraries)
        _update_project_data(self.window, data)
