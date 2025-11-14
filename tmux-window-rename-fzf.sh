#!/usr/bin/env bash

# Get current window name
current_name=$(tmux display-message -p '#W')

# Open tmux popup
tmux display-popup -E "bash -c '
  # fzf prompt on same line, editable
  new_name=\$(echo \"$current_name\" | fzf \
    --print-query \
    --height=1 \
    --border=rounded \
    --prompt=\"Rename window: \" \
    --no-sort \
    --ansi \
    --exit-0)

  # fzf outputs query + selection; we take the first line
  new_name=\$(echo \"\$new_name\" | head -n1)

  if [ -n \"\$new_name\" ] && [ \"\$new_name\" != \"$current_name\" ]; then
    tmux rename-window \"\$new_name\"
    echo -e \"\033[1;32mRenamed to:\033[0m \$new_name\"
    sleep 1
  else
    echo -e \"\033[1;31mCanceled or unchanged\033[0m\"
    sleep 1
  fi
'"