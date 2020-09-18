ls -R vscode-lua
ls -R LSP-lua-source

VSCODE_LUA_DIR="${GITHUB_WORKSPACE}/vscode-lua"
LSP_LUA_SOURCE_DIR="${GITHUB_WORKSPACE}/LSP-lua-source"

function process
{
    local OUT_DIR="${GITHUB_WORKSPACE}/out/LSP-lua-$1"
    local BIN_DIR="${VSCODE_LUA_DIR}/bin/$2"
    mkdir -p out/$1
    pushd "${OUT_DIR}"
        mkdir -p bin/$2
        cp "${BIN_DIR}"/* bin/$2/
        chmod +x bin/$2/*
        cp -R "${VSCODE_LUA_DIR}/server/libs" .
        cp -R "${VSCODE_LUA_DIR}/server/locale" .
        cp -R "${VSCODE_LUA_DIR}/server/script" .
        cp "${VSCODE_LUA_DIR}/server/main.lua" .
        cp -R "${VSCODE_LUA_DIR}/server/platform.lua" .
        cp "${LSP_LUA_SOURCE_DIR}/plugin.py" .
        cp "${LSP_LUA_SOURCE_DIR}/LSP-lua.sublime-commands" .
        cp "${LSP_LUA_SOURCE_DIR}/LSP-lua.sublime-settings" .
        cp "${LSP_LUA_SOURCE_DIR}/LICENSE" .
        cp "${LSP_LUA_SOURCE_DIR}/NOTICE" .
        touch .no-sublime-package
    popd
    zip LSP-lua-$1.zip "${OUT_DIR}"
}

process linux Linux
process osx macOS
process windows Windows

ls -lash
