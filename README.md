# Pi-hole Display

## Introduction

The Pi-hole Display Controller is a Python application designed to run on a Raspberry Pi with an attached LCD display. It provides a user interface for monitoring Pi-hole statistics and performing system maintenance tasks through physical button controls.

The application works in conjunction with the Pi-hole Admin Display Dashboard (PADD) to provide both visual feedback and control capabilities. It uses the four built-in buttons on the PiTFT 2.8" Plus 320x240 TFT display for functions like dimming the display, updating Pi-hole, and shutting down the system for maintenance.

The application starts automatically on boot using a startup script called from `.bashrc`.

<img src="doc/img/PiHole_TFT_buttons.jpg" style=" width:480px; " >

## How to Use the Buttons

The PiTFT 2.8" display has four buttons on the side. The application uses a **menu-based system** where buttons have different functions depending on the current mode:

- **Normal mode**: Displays PADD
- **Pi-Hole Update Menu**: Triggered by holding Button 1
- **System Control Menu**: Triggered by holding Button 2

### Button Layout (Top to Bottom)

```
┌─────────────┐
│  Button 1   │ ← Top button
├─────────────┤
│  Button 2   │
├─────────────┤
│  Button 3   │
├─────────────┤
│  Button 4   │ ← Bottom button
└─────────────┘
```

---

## Normal Mode (PADD Display)

When the display shows PADD:

**Button 1** - Brightness & Menu
- **Press**: Dim the display
- **Hold 2 seconds**: Open the **Pi-Hole Update Menu**

**Button 2** - System Menu
- **Hold 2 seconds**: Open the **System Control Menu**

**Buttons 3 & 4**
- Not used in normal mode

---

## Pi-Hole Update Menu

**How to access**: Hold Button 1 for two seconds

The display shows your options:

```
+---------------------------------+
|       Pi-Hole Update Menu       |
+---------------------------------+

Button 2: Update Gravity
Button 3: Update Pi-hole
Button 4: Update PADD

Waiting 30s for selection
Any other button cancels
```

**What each button does:**

- **Button 1: Cancel**
  - Returns to PADD display

- **Button 2: Update Gravity**
  - Updates Pi-hole's blocklists. Use this after adding new blocklists or to refresh ad-blocking lists. Shows download progress and takes 1-3 minutes.

- **Button 3: Update Pi-hole**
  - Updates Pi-hole core software to the latest version. Use when an update is available. Shows update progress and takes 2-5 minutes. May require a reboot afterward.

- **Button 4: Update PADD**
  - Updates the PADD dashboard display from GitHub. Shows what changed. Takes less than 1 minute.

All updates display progress in real-time and show error messages if something fails. The menu times out after 30 seconds.

---

## System Control Menu

**How to access**: Hold Button 2 for two seconds

The display shows your options:

```
+--------------------------------+
|      System Control Menu       |
+--------------------------------+

Button 2: Update System
Button 3: Restart System
Button 4: Shutdown System

Waiting 30s for selection...
Any other button cancels
```

**What each button does:**

- **Button 1: Cancel**
  - Returns to PADD display

- **Button 2: Update System**
  - Updates Raspberry Pi OS and all installed packages. Runs `apt update`, `apt full-upgrade`, and `apt autoremove`. Shows update progress and may take 5-15 minutes depending on available updates.

- **Button 3: Restart System**
  - Reboots the Raspberry Pi. The display will go dark and restart within 1-2 minutes.

- **Button 4: Shutdown System**
  - Safely shuts down the Raspberry Pi. Unplug power only after the display goes dark and activity LED stops blinking.

The menu times out after 30 seconds.

---

## Tips

- When you enter a menu, the display automatically switches to full brightness
- All operations show their progress on the display
- Check the logs at `~/pihole_display/log/pihole_display.log` for details


## Requirements

### Hardware

* A Raspberry Pi (tested on a model 3B and 3B+)

* Display and enclosure---modify/customize enclosure as you prefer, this is what I did:
  - Adafruit PiTFT Plus 320x240 2.8" TFT
    - https://www.adafruit.com/product/2423
  - Faceplate and Buttons Pack for 2.8" PiTFTs
    - https://www.adafruit.com/product/2807
  - Pi Model B+ / Pi 2 / Pi 3 - Case Base and Faceplate Pack - Clear - for 2.8" PiTFT
    - https://www.adafruit.com/product/3062

<img src="doc/img/PiTFT_buttons_parts.jpg" style=" width:480px; " >



### Software

* Raspberry Pi OS Lite
  - Tested on: "Raspberry Pi OS 12 (bookworm)"
  - https://www.raspberrypi.org/software/operating-systems/

* Python 3

* git

* tmux

* Adafruit Raspberry Pi Installer scripts
  - https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi

* Pi-Hole (optional, but this is what I'm using it for)

* PADD (Pi-hole Admin Display Dashboard)
  - **Included as a git submodule** - automatically cloned when using `--recurse-submodules`
  - https://github.com/pi-hole/PADD

* Python packages (see requirements.txt):
  - gpiozero (tested on Version 1.5.1 or later)
  - PyYAML
  - pigpio
  - setuptools

## Installation

### Hardware

#### PiTFT Plus 2.8" TFT connected to Pi 40-pin GPIO connector

<img src="doc/img/PiTFT_plugin.jpg" style=" width:480px; " >

### Software

#### PiHole
* Install PiHole and get it up and running for your network
  - https://docs.pi-hole.net/main/basic-install/
* If you already have PiHole running, move along...

#### pip3
If you don't have pip3, install it with
```
sudo apt install python3-pip
```

#### Git and tmux
Install git and tmux:
```
sudo apt install git tmux
```

#### Get pihole_display (this repository)
**Important:** Use `--recurse-submodules` to automatically clone the PADD submodule:
```
cd ~
git clone --recurse-submodules https://github.com/andersix/pihole_display.git
```

If you already cloned without submodules, initialize them:
```
cd ~/pihole_display
git submodule update --init --recursive
```

**Note:** PADD is now included as a git submodule and configured by default in `config/config.yaml`. If you prefer to use a different PADD installation location, you can edit the `paths.padd_dir` and `paths.padd_script` settings in the config file.

#### pigpio
If you don't have pigpio, install it with
```
sudo apt install pigpio
```
* enter ```sudo raspi-config``` on the command line, and enable Remote GPIO.
  - select "3 Interface Options", then "P8 Remote GPIO", then "Yes" to enable.
  - select OK then Finish to exit raspi-config
* enable and start the gpio service
  - ```sudo systemctl enable pigpiod```
  - ```sudo systemctl start pigpiod```
  - NOTE: starting and enabling the pigpiod service will not allow remote connections unless configured accordingly, but that's OK since we're only using it locally.

#### Get the Adafruit installer scripts for the PiTFT:
```
cd ~
sudo pip3 install --upgrade adafruit-python-shell click==7.0
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts
```

#### Pick the appropriate installer
I'm using the PiTFT 2.8 Capacitive, so am using:
```
sudo python3 adafruit-pitft.py --display=28c --rotation=90 --install-type=console
```
* for other displays, or details, check here:
  - https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/easy-install-2
  
#### Reboot and return to here
Once the PiTFT script is installed, reboot your Pi, and return to the next step below.

#### Enable Auto-Login (Required)
The display controller requires auto-login to start automatically on boot.

Configure auto-login using raspi-config:
```bash
sudo raspi-config
```
- Select "1 System Options"
- Select "S5 Boot / Auto Login"
- Select "B2 Console Autologin" (Text console, automatically logged in as 'pi' user)
- Select Finish and reboot if prompted

#### Change the console font
* Edit the /boot/cmdline.txt file and to the end of the line, after "rootwait", add:
```
fbcon=map:10 fbcon=font:VGA8x8
```
Save the file, and it should have
```
$ cat /boot/cmdline.txt
console=serial0,115200 console=tty1 root=PARTUUID=XXXXXXXX-XX rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait fbcon=map:10 fbcon=font:VGA8x8
```
(NOTE: don't change the value for the PARTUUID in your cmdline.txt file)

##### Improve console font
Run the command
```
sudo dpkg-reconfigure console-setup
```
and go select the following options to get Terminus 6x12
* Encoding:
  - UTF-8
* Character set to support:
  - Guess optimal character set
* Font for the console:
  - Terminus
* Font size:
  - 6x12 (framebuffer only)

#### Install Python Dependencies

Install the required Python packages:
```bash
cd ~/pihole_display
sudo pip3 install -r requirements.txt
```

#### Add User to Pi-hole Group

Pi-hole requires authentication for PADD. Add your user to the pihole group:
```bash
sudo usermod -G pihole pi
```

See https://github.com/pi-hole/PADD?tab=readme-ov-file#authentication for details and other options.

#### Verify pigpiod is Running

The pigpio daemon should already be running from the earlier setup step. Verify it:
```bash
sudo systemctl status pigpiod
```

If not running, start it:
```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

#### Configure Display Controller to Start at Boot

**Important:** This assumes your Raspberry Pi is configured for auto-login on boot (configured earlier).

Edit the pi user's `~/.bashrc` and add the following code **at the very top** of the file:

```bash
# Run PiHole display controller
if [ "$TERM" == "linux" ] ; then
  if [ -f /home/pi/pihole_display/scripts/start_display.sh ]; then
      /home/pi/pihole_display/scripts/start_display.sh
      return 0
  fi
fi
```

This startup script (`scripts/start_display.sh`) automatically:
- Creates a tmux session with two windows
- Starts PADD in the first window to display Pi-hole statistics
- Starts the button controller (`main.py`) in the second window
- Switches to the PADD window for display
- Logs startup details to `log/startup.log`

**Note:** If you want to customize the PADD location, edit `config/config.yaml` and update the `paths.padd_dir` and `paths.padd_script` settings.

#### Final Reboot

Reboot your Pi to start the display controller:
```bash
sudo reboot
```

After reboot, the display should show the PADD status screen for your Pi-hole, and the buttons should be working as described earlier.

That's it! If you have issues, see the Troubleshooting section below.

## Troubleshooting

### Check if the tmux session is running
```bash
tmux list-sessions
```
You should see a session named "display". If not, the startup script may have failed.

### Check startup logs
```bash
cat ~/pihole_display/log/startup.log
```
This shows detailed information about the tmux session creation and startup process.

### Check application logs
```bash
tail -f ~/pihole_display/log/pihole_display.log
```
This shows runtime logs from the Python application, including button presses and any errors.

### Verify pigpiod is running
```bash
sudo systemctl status pigpiod.service
```
You should see "Active: active (running)". If not:
```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Check if Python process is running
```bash
pgrep -f "main.py"
```
Should return a process ID. If not, the controller isn't running.

### Attach to the tmux session to see what's happening
```bash
tmux attach -t display
```
- Press `Ctrl+b` then `w` to see and select between windows
- Press `Ctrl+b` then `d` to detach without stopping the session

### Common Issues

**Buttons not responding:**
- Verify Python process is running: `pgrep -f main.py`
- Check that pigpiod is running
- Review application logs for GPIO errors
- Check for syntax errors if you modified the code

**Display not showing PADD:**
- Verify tmux session exists: `tmux ls`
- Check PADD submodule is initialized: `ls ~/pihole_display/PADD/padd.sh`
- Review startup logs: `cat ~/pihole_display/log/startup.log`

**Application won't start on boot:**
- Verify auto-login is enabled: `sudo raspi-config`
- Check .bashrc has startup code at the top
- Verify file paths in the .bashrc code match your installation

## Updates

### Updating the Application

When there are updates to this project:
```bash
cd ~/pihole_display
git pull
git submodule update --remote --merge  # Update PADD submodule

# Restart the application by killing the tmux session
tmux kill-session -t display
# Then manually run the startup script or reboot
/home/pi/pihole_display/scripts/start_display.sh
```

### Update History

* **2025-11-02**
  - PADD is now included as a git submodule
  - Configuration centralized in `config/config.yaml`
  - Modular architecture with separate controllers for display, buttons, PiHole, and system operations
  - Menu system with confirmation timeout for safer operation

* **2022-5-09**
  - Now using the pigpio factory for PWM control to eliminate backlight flicker when dimmed
  - Updated buttons to use press-and-hold (2 second) pattern for menu activation

## Modifications and Improvements

Submit pull requests. Go for it. You can do it.
