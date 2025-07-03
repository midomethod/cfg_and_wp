# ZSH_THEME="sunrise" # set by `omz`

# source /usr/share/cachyos-zsh-config/cachyos-config.zsh
# POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true

# Location and size of your history file
HISTFILE=~/.zsh_history
HISTSIZE=10000           # Number of commands to keep in memory
SAVEHIST=10000           # Number of commands to save to the history file

# History behavior options
setopt INC_APPEND_HISTORY       # Save commands immediately (not just on shell exit)
setopt SHARE_HISTORY            # Share history across all sessions
setopt HIST_IGNORE_DUPS         # Ignore duplicate commands
setopt HIST_IGNORE_SPACE        # Ignore commands that start with a space
setopt HIST_REDUCE_BLANKS       # Remove superfluous blanks before storing

# Optional: bind up/down arrow to history search
# bindkey "^[[A" up-line-or-search
# bindkey "^[[B" down-line-or-search

export EDITOR=nvim;
export PATH=$HOME/bin:$PATH;

bindkey -v # Have this disabled for now because of vim skill issue
bindkey '^A' beginning-of-line
bindkey '^E' end-of-line

eval "$(starship init zsh)";

y() {
	local tmp
	tmp="$(mktemp -t yazi-cwd.XXXXXX)" || return
	yazi "$@" --cwd-file="$tmp"
	local cwd
	cwd="$(<"$tmp")"
	[ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && cd -- "$cwd"
	rm -f -- "$tmp"
}
