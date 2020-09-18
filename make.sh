set -e

VSCODE_LUA_DIR="${GITHUB_WORKSPACE}/vscode-lua"
LSP_LUA_SOURCE_DIR="${GITHUB_WORKSPACE}/LSP-lua-source"

function process
{
    local OUT_DIR="${GITHUB_WORKSPACE}/out/LSP-lua-$1"
    local BIN_DIR="${VSCODE_LUA_DIR}/bin/$2"
    mkdir -p "${OUT_DIR}/bin/$2"
    cp "${BIN_DIR}"/* bin/$2/
    chmod +x "${OUT_DIR}"/bin/$2/*
    cp -R "${VSCODE_LUA_DIR}/server/libs" "${OUT_DIR}/"
    cp -R "${VSCODE_LUA_DIR}/server/locale" "${OUT_DIR}/"
    cp -R "${VSCODE_LUA_DIR}/server/script" "${OUT_DIR}/"
    cp "${VSCODE_LUA_DIR}/server/main.lua" "${OUT_DIR}/"
    cp "${VSCODE_LUA_DIR}/server/platform.lua" "${OUT_DIR}/"
    cp "${LSP_LUA_SOURCE_DIR}/plugin.py" "${OUT_DIR}/"
    cp "${LSP_LUA_SOURCE_DIR}/LSP-lua.sublime-commands" "${OUT_DIR}/"
    cp "${LSP_LUA_SOURCE_DIR}/LSP-lua.sublime-settings" "${OUT_DIR}/"
    cp "${LSP_LUA_SOURCE_DIR}/LICENSE" "${OUT_DIR}/"
    cp "${LSP_LUA_SOURCE_DIR}/NOTICE" "${OUT_DIR}/"
    touch "${OUT_DIR}/.no-sublime-package"
    patch "${OUT_DIR}/main.lua" "${LSP_LUA_SOURCE_DIR}/patch.diff"
    zip LSP-lua-$1.zip "${OUT_DIR}"
}

process linux Linux
process osx macOS
process windows Windows

ls -lash LSP-lua-linux
ls -lash LSP-lua-osx
ls -lash LSP-lua-windows
