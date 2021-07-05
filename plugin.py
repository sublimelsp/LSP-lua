from LSP.plugin import AbstractPlugin
from LSP.plugin import register_plugin
from LSP.plugin import unregister_plugin
from LSP.plugin import DottedDict
from LSP.plugin.core.typing import Any, Callable, List, Dict, Mapping, Optional, Tuple
import sublime
import os
import urllib.request
import zipfile
import shutil
import tempfile


URL = "https://github.com/sumneko/vscode-lua/releases/download/v{0}/lua-{0}.vsix"


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
    def zipfile(cls) -> str:
        return os.path.join(cls.basedir(), "lua.vsix")

    @classmethod
    def binplatform(cls) -> str:
        return {
            "linux": "Linux",
            "windows": "Windows",
            "osx": "macOS"
        }[sublime.platform()]

    @classmethod
    def bindir(cls) -> str:
        return os.path.join(cls.basedir(), "bin", cls.binplatform())

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
            binplatform = cls.binplatform()
            with tempfile.TemporaryDirectory() as tmp:
                # Download the VSIX file
                zip_file = os.path.join(tmp, "lua.vsix")
                urllib.request.urlretrieve(URL.format(server_version), zip_file)
                # VSIX files are just zipfiles
                with zipfile.ZipFile(zip_file, "r") as z:
                    z.extractall(tmp)
                for root, dirs, files in os.walk(os.path.join(tmp, "extension", "server", "bin")):
                    for d in dirs:
                        if d != binplatform:
                            shutil.rmtree(os.path.join(root, d))
                for root, dirs, files in os.walk(os.path.join(tmp, "extension", "server", "bin", binplatform)):
                    for file in files:
                        os.chmod(os.path.join(root, file), 0o744)
                # Make sure package storage path exists for new users
                os.makedirs(cls.storage_path(), exist_ok=True)
                # Move the relevant subdirectory to the package storage
                os.rename(os.path.join(tmp, "extension", "server"), cls.basedir())
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
            "binplatform": {
                "linux": "Linux",
                "windows": "Windows",
                "osx": "macOS"
            }[sublime.platform()],
            "locale": str(settings.get("locale"))
        }

    def on_pre_server_command(self, command: Mapping[str, Any], done_callback: Callable[[], None]) -> bool:
        cmd = command["command"]
        if cmd == "lua.config":
            return self._handle_lua_config_command(command["arguments"], done_callback)
        return super().on_pre_server_command(command, done_callback)

    def _handle_lua_config_command(self, args: List[Dict[str, Any]], done_callback: Callable[[], None]) -> bool:
        action = args[0]["action"]
        if action == "add":
            key = args[0]["key"]
            value = args[0]["value"]
            session = self.weaksession()
            if not session:
                return False
            window = session.window
            data = window.project_data()
            if not isinstance(data, dict):
                return False
            dd = DottedDict(data)
            key = "settings.LSP.LSP-lua.settings.{}".format(key)
            thelist = dd.get(key)
            if isinstance(thelist, list):
                if value not in thelist:
                    thelist.append(value)
            else:
                thelist = [value]
            dd.set(key, thelist)
            data = dd.get()
            window.set_project_data(data)
            done_callback()
            return True
        return False


def plugin_loaded() -> None:
    register_plugin(Lua)


def plugin_unloaded() -> None:
    unregister_plugin(Lua)
