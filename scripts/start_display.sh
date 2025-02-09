#!/bin/bash

# Log startup:
LOG_FILE="/home/pi/pihole_display/log/startup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_msg() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# check tmux session
check_session_health() {
    if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        log_msg "ERROR: Tmux session lost"
        return 1
    fi
    
    if ! tmux list-windows -t "$SESSION_NAME" | grep -q "$PADD_WINDOW"; then
        log_msg "ERROR: PADD window not found"
        return 1
    fi
    
    if ! tmux list-windows -t "$SESSION_NAME" | grep -q "$CONTROL_WINDOW"; then
        log_msg "ERROR: Control window not found"
        return 1
    fi
    
    return 0
}

# Clear log file at start
> "$LOG_FILE"
log_msg "Starting display controller setup"

# Check if we're on the PiTFT screen (ssh is xterm)
if [ "$TERM" == "linux" ] ; then
    # Load config values if available
    CONFIG_FILE="/home/pi/pihole_display/config/config.yaml"
    if [ -f "$CONFIG_FILE" ]; then
        log_msg "Found config file"
        SESSION_NAME=$(yq '.display.tmux.session_name' "$CONFIG_FILE" | tr -d '"')
        PADD_WINDOW=$(yq '.display.tmux.padd_window' "$CONFIG_FILE" | tr -d '"')
        CONTROL_WINDOW=$(yq '.display.tmux.control_window' "$CONFIG_FILE" | tr -d '"')
        PADD_SCRIPT=$(yq '.paths.padd_script' "$CONFIG_FILE" | tr -d '"')
        PYTHON_PATH=$(yq '.paths.python_path' "$CONFIG_FILE" | tr -d '"')
        MAIN_SCRIPT=$(yq '.paths.main_script' "$CONFIG_FILE" | tr -d '"')
    else
        log_msg "WARNING: Config file not found, using defaults"
        SESSION_NAME="display"
        PADD_WINDOW="padd"
        CONTROL_WINDOW="control"
        PADD_SCRIPT="/home/pi/PADD/padd.sh"
        PYTHON_PATH="/usr/bin/python3"
        MAIN_SCRIPT="/home/pi/pihole_display/main.py"
    fi

    log_msg "Configuration values:"
    log_msg "- tmux:"
    log_msg "  - SESSION_NAME:   $SESSION_NAME"
    log_msg "  - PADD_WINDOW:    $PADD_WINDOW"
    log_msg "  - CONTROL_WINDOW: $CONTROL_WINDOW"
    log_msg "- paths:"
    log_msg "  - PADD_SCRIPT:    $PADD_SCRIPT"
    log_msg "  - PYTHON_PATH:    $PYTHON_PATH"
    log_msg "  - MAIN_SCRIPT:    $MAIN_SCRIPT"

    # Verify files exist
    if [ -f "$PADD_SCRIPT" ]; then
        log_msg "PADD script found: $PADD_SCRIPT"
    else
        log_msg "ERROR: PADD script not found: $PADD_SCRIPT"
        exit 1
    fi

    if [ -f "$MAIN_SCRIPT" ]; then
        log_msg "Main script found: $MAIN_SCRIPT"
    else
        log_msg "ERROR: Main script not found: $MAIN_SCRIPT"
        exit 1
    fi

    # Check if tmux is running
    tmux ls &> /dev/null
    TMUX_RUNNING=$?
    log_msg "Tmux running status: $TMUX_RUNNING"

    # Create or attach to tmux session
    if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        log_msg "Creating new tmux session"
        
        # Create new tmux session with first window running PADD
        tmux new-session -d -s "$SESSION_NAME" -n "$PADD_WINDOW" "$PADD_SCRIPT"
        PADD_WINDOW_CREATED=$?
        log_msg "PADD window creation status: $PADD_WINDOW_CREATED"
        
        if [ $PADD_WINDOW_CREATED -ne 0 ]; then
            log_msg "ERROR: Failed to create PADD window"
            exit 1
        fi
        
        # Wait for session to be fully created
        sleep 2
        
        # Verify tmux session exists
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            log_msg "Session created successfully"
            
            # Disable tmux status line
            tmux set-option -t "$SESSION_NAME" status off
            sleep 1
            
            # Create second tmux window and send command
            log_msg "Creating control window"
            tmux new-window -t "$SESSION_NAME:1" -n "$CONTROL_WINDOW"
            CONTROL_WINDOW_CREATED=$?
            
            if [ $CONTROL_WINDOW_CREATED -eq 0 ]; then
                log_msg "Control window created, sending Python command"
                sleep 1
                tmux send-keys -t "$SESSION_NAME:$CONTROL_WINDOW" "$PYTHON_PATH $MAIN_SCRIPT" Enter
                log_msg "Python command sent to control window"
                
                # Verify Python process started
                sleep 2
                if pgrep -f "$MAIN_SCRIPT" > /dev/null; then
                    log_msg "Python controller successfully started"
                    
                    # Check for successful initialization message
                    if tmux capture-pane -t "$SESSION_NAME:$CONTROL_WINDOW" -p | grep -q "PiHole Display started successfully"; then
                        log_msg "Control window initialization verified"
                    else
                        log_msg "WARNING: Control window may not have initialized properly"
                    fi
                else
                    log_msg "ERROR: Python controller failed to start"
                    exit 1
                fi
            else
                log_msg "ERROR: Failed to create control window"
                exit 1
            fi
            
            # Verify tmux session health
            if ! check_session_health; then
                log_msg "ERROR: Session health check failed"
                exit 1
            fi
            
            # Select PADD tmux window as default
            sleep 1
            tmux select-window -t "$SESSION_NAME:$PADD_WINDOW"
            
            # List tmux windows to verify creation
            log_msg "Current tmux windows:"
            tmux list-windows -t "$SESSION_NAME" >> "$LOG_FILE" 2>&1
        else
            log_msg "ERROR: Failed to create tmux session"
            exit 1
        fi
    else
        log_msg "Session already exists"
        # Verify existing tmux session health
        if ! check_session_health; then
            log_msg "ERROR: Existing session health check failed"
            exit 1
        fi
    fi
    
    # Attach to tmux session if we're on tty1
    if [ "$(tty)" == "/dev/tty1" ]; then
        log_msg "Attaching to tmux session"
        exec tmux attach-session -t "$SESSION_NAME"
    fi
fi

