#!/bin/bash

# If we're on the PiTFT screen (ssh is xterm)
if [ "$TERM" == "linux" ] ; then
    # Create or attach to tmux session
    if ! tmux has-session -t display 2>/dev/null; then
        # Create new session with first window running PADD
        tmux new-session -d -s display -n padd '/home/pi/PADD/padd.sh'
        
        # Disable status line
        tmux set-option -t display status off
        
        # Create second window for pihole display control
        tmux new-window -t display:1 -n control
        
        # Select PADD window as default
        tmux select-window -t display:padd
    fi
    
    # Attach to session if we're on tty1
    if [ "$(tty)" == "/dev/tty1" ]; then
        exec tmux attach-session -t display
    fi
fi
