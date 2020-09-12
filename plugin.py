from LSP.plugin import AbstractPlugin
from LSP.plugin.core.typing import Dict, Optional
import sublime


class Lua(AbstractPlugin):
    @classmethod
    def name(cls) -> str:
        return cls.__name__.lower()

    @classmethod
    def additional_variables(cls) -> Optional[Dict[str, str]]:
        settings = sublime.load_settings("LSP-lua.sublime-settings")
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
