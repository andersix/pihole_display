# Startup code

  - Add the following to the beginning of your .bashrc file
  - This will run the start_display.sh script at login
  - Make sure your PiHole with LCD display is set to login automaticaly

```
# Run PiHole display controller
if [ "$TERM" == "linux" ] ; then
  if [ -f /home/pi/pihole_display/scripts/start_display.sh ]; then
      /home/pi/pihole_display/scripts/start_display.sh
      return 0
  fi
fi
```

