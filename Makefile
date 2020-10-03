ifndef VSCODE_LUA_GIT_TAG
$(error VSCODE_LUA_GIT_TAG is not set)
endif

all: \
	out/windows-x64/release.zip \
	out/osx-x64/release.zip \
	out/linux-x64/release.zip

BINDIR_windows-x64 = Windows
BINDIR_osx-x64 = macOS
BINDIR_linux-x64 = Linux

VSCODE_LUA = vscode-lua-$(VSCODE_LUA_GIT_TAG)

SOURCE = \
	plugin.py \
	LSP-lua.sublime-commands \
	LSP-lua.sublime-settings \
	NOTICE \
	LICENSE

FILES = \
	$(VSCODE_LUA)/server/libs \
	$(VSCODE_LUA)/server/locale \
	$(VSCODE_LUA)/server/script \
	$(VSCODE_LUA)/server/main.lua \
	$(VSCODE_LUA)/server/platform.lua \
	$(SOURCE)

out/%/release.zip: $(VSCODE_LUA) $(SOURCE) patch.diff
	mkdir -p out/$*/bin/$(BINDIR_$*)
	rsync -a $(FILES) out/$*/
	rsync -a $(VSCODE_LUA)/bin/$(BINDIR_$*)/ out/$*/bin/$(BINDIR_$*)
	chmod +x out/$*/bin/$(BINDIR_$*)/*
	patch out/$*/main.lua patch.diff
	touch out/$*/.no-sublime-package
	cd out/$* && zip -q -r release.zip .

$(VSCODE_LUA):
	git clone --depth=1 --recursive --branch=$(VSCODE_LUA_GIT_TAG) https://github.com/sumneko/vscode-lua.git $(VSCODE_LUA)

clean:
	rm -rf out $(VSCODE_LUA)

.PHONY: all clean
