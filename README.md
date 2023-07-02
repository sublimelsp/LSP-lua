# LSP-lua

A language client for Lua. This package will download and unpack the [lua-language-server](https://github.com/sumneko/lua-language-server) in `$DATA/Package Storage/LSP-lua`.

To use this package, you must have:

- The [LSP](https://packagecontrol.io/packages/LSP) package.

# Applicable Selectors

This language server operates on files with the `source.lua` base scope.

# Configuration

Run `Preferences: LSP-lua Settings` from the Command Palette to tweak the settings.

# Embedded Environment

Lua is an embeddable language. This means it is usually part of a larger application, like [OpenResty](https://openresty.org/en/) or [LÖVE](https://love2d.org/). This language server has a few built-in third-party environments ready for use. The environment is set up via sublime project settings. As such, if you want to persist these settings you need to use a [.sublime-project](https://www.sublimetext.com/docs/projects.html) file. This project file can be created automatically by clicking on

    Project > Save Project As...

You can choose one of the built-in environments by running the command

    LSP-lua: Setup Environment

from the Command Palette.

To set up an environment that is not provided by the language server itself, you will need to modify the `Lua.workspace.userThirdParty` server setting.

Setting up the right embedded environment is essential for accurate auto-completion.

# Locale

You can make this language server report documentation in English or Chinese. The default is English. To change it
into Chinese, run the command `Preferences: LSP-lua Settings` and change the `"locale"` key.

# Popup highlighting

The code blocks that this language server returns are not valid Lua code. Consequently the built-in syntax highlighter marks most code blocks as invalid. Set

```js
    "mdpopups.use_sublime_highlighter": false,
````

in Packages/User/Preferences.sublime-settings to use pygments instead, which is a highlighter that is more forgiving.

# Disabling Diagnostics via Code Actions

This language server allows you to disable diagnostics by means of a Code Action. You can run the "Code Action" and the client (this package) is supposed to modify the settings to add or remove the unwanted diagnostic. This package implements that by editing your .sublime-project file. So in order for this to work, you need to have your window be backed by a .sublime-project file. [Learn more about projects here](https://www.sublimetext.com/docs/projects.html).
