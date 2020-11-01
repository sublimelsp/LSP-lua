from LSP.plugin import AbstractPlugin
from LSP.plugin import register_plugin
from LSP.plugin import unregister_plugin
from LSP.plugin.core.typing import Dict, Optional, Tuple
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


def plugin_loaded() -> None:
    register_plugin(Lua)


def plugin_unloaded() -> None:
    unregister_plugin(Lua)
