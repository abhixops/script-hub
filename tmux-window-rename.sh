#!/usr/bin/env bash

# Get current window name
current_name=$(tmux display-message -p '#W')

# Use tmux popup to prompt for new name
tmux display-popup -w 30% -h 18% -E "
  echo '\033[1;36mRename window:\033[0m'
  echo '---------------'
  echo 'Current: \033[1;33m$current_name\033[0m'
  echo -n 'New name: '
  read new_name
  if [ -n \"\$new_name\" ]; then
    tmux rename-window \"\$new_name\"
  else
    echo '\033[1;31mCanceled (empty name)\033[0m'
    sleep 1
  fi
"