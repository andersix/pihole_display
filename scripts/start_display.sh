#!/bin/bash

# Determine script and project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Log startup
LOG_FILE="$PROJECT_DIR/log/startup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_msg() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Rotate old log
if [ -f "$LOG_FILE" ]; then
    mv "$LOG_FILE" "$LOG_FILE.old" 2>/dev/null
fi

log_msg "Starting display controller setup"
log_msg "Script directory: $SCRIPT_DIR"
log_msg "Project directory: $PROJECT_DIR"

# Cleanup function for error handling
cleanup_on_error() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ -n "$SESSION_NAME" ]; then
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            log_msg "Cleaning up failed session due to error (exit code: $exit_code)"
            tmux kill-session -t "$SESSION_NAME" 2>/dev/null
        fi
    fi
}

# Check tmux session health
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

# Check if Python controller process is running
check_python_running() {
    pgrep -f "python.*$MAIN_SCRIPT" > /dev/null
}

# Wait for Python process to start and stabilize
wait_for_python() {
    local max_attempts=10
    log_msg "Waiting for Python controller to start"

    for i in $(seq 1 $max_attempts); do
        sleep 1
        if check_python_running; then
            # Give it one more second to potentially crash on initialization
            sleep 1
            if check_python_running; then
                log_msg "Python controller successfully started (attempt $i/$max_attempts)"
                return 0
            fi
        fi
    done

    log_msg "ERROR: Python controller failed to start after $max_attempts attempts"
    return 1
}

# Restart Python controller in existing session
restart_python_controller() {
    log_msg "Restarting Python controller in control window"
    tmux send-keys -t "$SESSION_NAME:$CONTROL_WINDOW" C-c
    sleep 1
    tmux send-keys -t "$SESSION_NAME:$CONTROL_WINDOW" "$PYTHON_PATH $MAIN_SCRIPT" Enter

    if wait_for_python; then
        log_msg "Python controller restarted successfully"
        return 0
    else
        log_msg "ERROR: Failed to restart Python controller"
        return 1
    fi
}

# Check if we're on the PiTFT screen (ssh is xterm)
if [ "$TERM" == "linux" ] ; then
    # Set error trap
    trap cleanup_on_error EXIT

    # Load config values if available
    CONFIG_FILE="$PROJECT_DIR/config/config.yaml"

    if [ -f "$CONFIG_FILE" ]; then
        log_msg "Found config file: $CONFIG_FILE"

        # Check for yq dependency
        if ! command -v yq &> /dev/null; then
            log_msg "WARNING: yq not found, using default values"
            SESSION_NAME="display"
            PADD_WINDOW="padd"
            CONTROL_WINDOW="control"
            PADD_SCRIPT="$PROJECT_DIR/PADD/padd.sh"
            PYTHON_PATH="/usr/bin/python3"
            MAIN_SCRIPT="$PROJECT_DIR/main.py"
        else
            log_msg "Parsing config file with yq"
            SESSION_NAME=$(yq -r '.display.tmux.session_name' "$CONFIG_FILE" 2>/dev/null)
            PADD_WINDOW=$(yq -r '.display.tmux.padd_window' "$CONFIG_FILE" 2>/dev/null)
            CONTROL_WINDOW=$(yq -r '.display.tmux.control_window' "$CONFIG_FILE" 2>/dev/null)
            PADD_SCRIPT=$(yq -r '.paths.padd_script' "$CONFIG_FILE" 2>/dev/null)
            PYTHON_PATH=$(yq -r '.paths.python_path' "$CONFIG_FILE" 2>/dev/null)
            MAIN_SCRIPT=$(yq -r '.paths.main_script' "$CONFIG_FILE" 2>/dev/null)

            # Validate config values
            if [ -z "$SESSION_NAME" ] || [ "$SESSION_NAME" == "null" ]; then
                log_msg "WARNING: Invalid session_name in config, using default"
                SESSION_NAME="display"
            fi
            if [ -z "$PADD_WINDOW" ] || [ "$PADD_WINDOW" == "null" ]; then
                PADD_WINDOW="padd"
            fi
            if [ -z "$CONTROL_WINDOW" ] || [ "$CONTROL_WINDOW" == "null" ]; then
                CONTROL_WINDOW="control"
            fi
            if [ -z "$PADD_SCRIPT" ] || [ "$PADD_SCRIPT" == "null" ]; then
                PADD_SCRIPT="$PROJECT_DIR/PADD/padd.sh"
            fi
            if [ -z "$PYTHON_PATH" ] || [ "$PYTHON_PATH" == "null" ]; then
                PYTHON_PATH="/usr/bin/python3"
            fi
            if [ -z "$MAIN_SCRIPT" ] || [ "$MAIN_SCRIPT" == "null" ]; then
                MAIN_SCRIPT="$PROJECT_DIR/main.py"
            fi
        fi
    else
        log_msg "WARNING: Config file not found, using defaults"
        SESSION_NAME="display"
        PADD_WINDOW="padd"
        CONTROL_WINDOW="control"
        PADD_SCRIPT="$PROJECT_DIR/PADD/padd.sh"
        PYTHON_PATH="/usr/bin/python3"
        MAIN_SCRIPT="$PROJECT_DIR/main.py"
    fi

    # Final validation - ensure no empty values
    if [ -z "$SESSION_NAME" ] || [ -z "$PADD_SCRIPT" ] || [ -z "$MAIN_SCRIPT" ]; then
        log_msg "ERROR: Critical configuration values are empty"
        exit 1
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

    # Create or attach to tmux session
    if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        log_msg "Creating new tmux session"

        # Create new tmux session with first window running PADD
        if ! tmux new-session -d -s "$SESSION_NAME" -n "$PADD_WINDOW" "$PADD_SCRIPT"; then
            log_msg "ERROR: Failed to create PADD window"
            exit 1
        fi
        log_msg "PADD window created successfully"

        # Wait for session to be fully created
        sleep 2

        # Verify tmux session exists
        if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            log_msg "ERROR: Failed to create tmux session"
            exit 1
        fi
        log_msg "Session created successfully"

        # Disable tmux status line
        tmux set-option -t "$SESSION_NAME" status off
        sleep 1

        # Create second tmux window without specifying index
        log_msg "Creating control window"
        if ! tmux new-window -t "$SESSION_NAME" -n "$CONTROL_WINDOW"; then
            log_msg "ERROR: Failed to create control window"
            exit 1
        fi
        log_msg "Control window created successfully"

        # Send Python command to control window
        sleep 1
        tmux send-keys -t "$SESSION_NAME:$CONTROL_WINDOW" "$PYTHON_PATH $MAIN_SCRIPT" Enter
        log_msg "Python command sent to control window"

        # Wait for Python process to start and stabilize
        if ! wait_for_python; then
            log_msg "ERROR: Python controller failed to start"
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

        log_msg "Display controller startup completed successfully"
    else
        log_msg "Session already exists"

        # Verify existing tmux session health
        if ! check_session_health; then
            log_msg "ERROR: Existing session health check failed"
            exit 1
        fi

        # Check if Python process is still running
        if ! check_python_running; then
            log_msg "WARNING: Python process not running, attempting restart"
            if ! restart_python_controller; then
                log_msg "ERROR: Failed to restart Python controller"
                exit 1
            fi
        else
            log_msg "Python controller is running"
        fi

        log_msg "Existing session verified and healthy"
    fi

    # Remove error trap on success
    trap - EXIT

    # Attach to tmux session if we're on tty1
    if [ "$(tty)" == "/dev/tty1" ]; then
        log_msg "Attaching to tmux session"
        exec tmux attach-session -t "$SESSION_NAME"
    fi
fi
