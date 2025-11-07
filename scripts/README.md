# Startup Script

## start_display.sh

This script automatically creates and manages the tmux session for the Pi-hole display controller.

### Usage

Add the following code to the **very top** of your `~/.bashrc` file:

**Important:** Your Raspberry Pi must be configured for auto-login (console autologin) for this to work.

```bash
# Run PiHole display controller
if [ "$TERM" == "linux" ] ; then
  if [ -f /home/pi/PhDC/scripts/start_display.sh ]; then
      /home/pi/PhDC/scripts/start_display.sh
      return 0
  fi
fi
```

### What it does

The `start_display.sh` script:
- Creates a tmux session named "display" with two windows
- Launches PADD (Pi-hole Admin Display Dashboard) in the first window
- Starts the Python button controller in the second window
- Switches to the PADD window for display
- Logs all startup activities to `../log/startup.log`

See the main [README.md](../README.md) for complete installation instructions.
