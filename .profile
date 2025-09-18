#!/bin/sh

# Adding all subfolders of ~/.local/bin to PATH
export PATH="$PATH:$(du -d 1 "$HOME/.local/bin/" | cut -f2 | tr "\n" ":" | sed "s/:*$//")"

# SSH/GPG config
export SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)
gpgconf --launch gpg-agent

