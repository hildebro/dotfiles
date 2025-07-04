source "/usr/share/fzf/key-bindings.zsh"
source "/usr/share/fzf/completion.zsh"

autoload -U colors && colors
autoload -U compinit && compinit
autoload -U promptinit && promptinit

# History settings
HISTFILE=~/.config/zsh/.zsh_history
HISTSIZE=10000
SAVEHIST=$HISTSIZE

# write to history immediately
setopt inc_append_history   
# ignore second instance of same event
setopt hist_ignore_dups     
# share history between session
setopt share_history        
# special history format with timestamp
setopt extended_history     
# fucking beep
setopt no_hist_beep         
# ignore entries with leading space
setopt hist_ignore_space    
# extended glob syntax
setopt extended_glob        
# print error if pattern matches nothing
setopt nomatch              
# report status of background jobs immediately
setopt notify               
# complete from both ends of a word
setopt complete_in_word     
# move cursor to the end of a completed word
setopt always_to_end        
# perform path search even on command names with slashes
setopt path_dirs            
# disable start/stop characters in shell editor
unsetopt flow_control       

# group matches and describe.
zstyle ':completion:*:matches' group 'yes'
zstyle ':completion:*:options' description 'yes'
zstyle ':completion:*:options' auto-description '%d'
zstyle ':completion:*:corrections' format ' %F{green}-- %d (errors: %e) --%f'
zstyle ':completion:*:descriptions' format ' %F{yellow}-- %d --%f'
zstyle ':completion:*:messages' format ' %F{yellow} -- %d --%f'
zstyle ':completion:*:warnings' format ' %F{red}-- no matches found --%f'
zstyle ':completion:*:default' list-prompt '%S%M matches%s'
zstyle ':completion:*' format ' %F{yellow}-- %d --%f'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' verbose yes

# fuzzy match mistyped completions.
zstyle ':completion:*' completer _complete _match _approximate
zstyle ':completion:*:match:*' original only
zstyle ':completion:*:approximate:*' max-errors 1 numeric

# directories
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*:*:cd:*' tag-order local-directories directory-stack path-directories
zstyle ':completion:*:*:cd:*:directory-stack' menu yes select
zstyle ':completion:*:-tilde-:*' group-order 'named-directories' 'path-directories' 'users' 'expand'
zstyle ':completion:*' squeeze-slashes true

# history
zstyle ':completion:*:history-words' stop yes
zstyle ':completion:*:history-words' remove-all-dups yes
zstyle ':completion:*:history-words' list false
zstyle ':completion:*:history-words' menu yes

# load aliases and shortcuts
[ -f "$HOME/.config/shortcutrc" ] && source "$HOME/.config/shortcutrc"
[ -f "$HOME/.config/aliasrc" ] && source "$HOME/.config/aliasrc"

# include hidden files in autocomplete
_comp_options+=(globdots)

# Prevent 'help' behavior of ^?, so it works as 'escape' mapping for vim mode
bindkey -v '^?' backward-delete-char

# faster switch to vim's normal mode
export KEYTIMEOUT=1

# change cursor shape for different vi modes.
function zle-keymap-select {
  if [[ ${KEYMAP} == vicmd ]] ||
     [[ $1 = 'block' ]]; then
    echo -ne '\e[1 q'

  elif [[ ${KEYMAP} == main ]] ||
       [[ ${KEYMAP} == viins ]] ||
       [[ ${KEYMAP} = '' ]] ||
       [[ $1 = 'beam' ]]; then
    echo -ne '\e[5 q'
  fi
}
zle -N zle-keymap-select

# initiate `vi insert` as keymap (can be removed if `bindkey -V` has been set elsewhere)
zle-line-init() {
    zle -K viins 
    echo -ne "\e[5 q"
}
zle -N zle-line-init

# Use beam shape cursor on startup.
echo -ne '\e[5 q'
# Use beam shape cursor for each new prompt.
preexec() { echo -ne '\e[5 q' ;}

# Use lf to switch directories and bind it to ctrl-o
lfcd () {
    tmp="$(mktemp)"
    lf -last-dir-path="$tmp" "$@"
    if [ -f "$tmp" ]; then
        dir="$(cat "$tmp")"
        rm -f "$tmp"
        if [ -d "$dir" ]; then
            if [ "$dir" != "$(pwd)" ]; then
                cd "$dir"
            fi
        fi
    fi
}
bindkey -s '^o' 'lfcd\n'

########## Janky solution for tab completion of project-specific ./bin folder ##########
# If the current directory has a ./bin folder,
# the absolute path to it is stored in this global.
typeset -g _current_dir_bin_path=""

# On dir change
chpwd() {
    local new_path=""
    local old_path_elements
    local element

    # If the previous dir had a bin folder,
    # remove it from PATH and clear out the global variable.
    if [[ -n "$_current_dir_bin_path" ]]; then
        # Split PATH into elements and filter out the old project path
        old_path_elements=("${(@ps/:/)PATH}") # Zsh specific split by ':'
        for element in "${old_path_elements[@]}"; do
            if [[ "$element" != "$_current_dir_bin_path" ]]; then
                if [[ -z "$new_path" ]]; then
                    new_path="$element"
                else
                    new_path="$new_path:$element"
                fi
            fi
        done
        PATH="$new_path"
        _current_dir_bin_path=""
    fi

    # If the new dir has a bin folder,
    # add it to PATH and fill the global variable.
    if [[ -d "./bin" ]]; then
        local project_bin_abs_path="$(pwd)/bin"

        # Ensure we don't add duplicate if somehow already there (shouldn't be after step 1)
        if ! print -l "$PATH" | grep -q "^${project_bin_abs_path}$"; then
            export PATH="${project_bin_abs_path}:$PATH"
            _current_dir_bin_path="$project_bin_abs_path" # Store the newly added path
            rehash # Rehash commands so zsh knows about new executables
        fi
    else
        # If no ./bin in the new directory, make sure _current_dir_bin_path is cleared
        _current_dir_bin_path=""
    fi
}

eval "$(starship init zsh)"
eval "$(zoxide init zsh)"

