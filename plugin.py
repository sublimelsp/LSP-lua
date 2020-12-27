from LSP.plugin import AbstractPlugin
from LSP.plugin import register_plugin
from LSP.plugin import unregister_plugin
from LSP.plugin import DottedDict
from LSP.plugin.core.typing import Any, Callable, List, Dict, Mapping, Optional, Tuple
import sublime


class Lua(AbstractPlugin):
    @classmethod
    def name(cls) -> str:
        return "LSP-{}".format(cls.__name__.lower())

    @classmethod
    def configuration(cls) -> Tuple[sublime.Settings, str]:
        base_name = "{}.sublime-settings".format(cls.name())
        file_path = "Packages/{}/{}".format(cls.name(), base_name)
        return sublime.load_settings(base_name), file_path

    @classmethod
    def additional_variables(cls) -> Optional[Dict[str, str]]:
        settings, _ = cls.configuration()
        locale = str(settings.get("locale"))
        binplatform = {
            "linux": "Linux",
            "windows": "Windows",
            "osx": "macOS"
        }[sublime.platform()]
        return {
            "binplatform": binplatform,
            "locale": locale
        }

    def on_pre_server_command(self, command: Mapping[str, Any], done_callback: Callable[[], None]) -> bool:
        cmd = command["command"]
        if cmd == "lua.config":
            return self._handle_lua_config_command(command["arguments"], done_callback)
        return super().on_pre_server_command(command, done_callback)

    def _handle_lua_config_command(self, args: List[Dict[str, Any]], done_callback: Callable[[], None]) -> bool:
        session = self.weaksession()
        if not session:
            return False
        window = session.window
        data = window.project_data()
        if not isinstance(data, dict):
            return False
        dd = DottedDict(data)
        dd.set("settings.LSP.LSP-lua.settings.{}".format(args[0]), args[1])
        done_callback()
        return True


def plugin_loaded() -> None:
    register_plugin(Lua)


def plugin_unloaded() -> None:
    unregister_plugin(Lua)
