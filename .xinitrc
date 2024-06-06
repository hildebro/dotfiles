#!/bin/sh

# Source files from etc
if [ -d /etc/X11/xinit/xinitrc.d ] ; then
 for f in /etc/X11/xinit/xinitrc.d/?*.sh ; do
  [ -x "$f" ] && . "$f"
 done
 unset f
fi

# Grab the session name given to starx via tuigreet
session=${2:-main}

# Switch to the appropriate branch for the session
/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME switch $session

[ -f ~/.xprofile ] && . ~/.xprofile

exec i3

