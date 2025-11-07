# Installation Guide

This guide walks you through setting up the Pi-hole Display Controller in three phases:
1. **Foundation** - Ensure your Raspberry Pi and Pi-hole are working
2. **Hardware** - Install and configure the PiTFT display
3. **Application** - Install the display controller software

---

## Phase 1: Foundation - Prerequisites

Before adding the display, ensure you have a working foundation.

### 1. Raspberry Pi with Operating System

You need a Raspberry Pi with Raspberry Pi OS installed and running:

- **Hardware**: Raspberry Pi 3B, 3B+, or 4 (RPi 5 not supported due to display driver compatibility)
- **Operating System**: Raspberry Pi OS Lite (recommended) or Desktop
- **Network**: Connected to your network with SSH access (recommended for setup)
- **Status**: Successfully booted and accessible

**Need to install Raspberry Pi OS?**
- Download: https://www.raspberrypi.org/software/operating-systems/
- Installation guide: https://www.raspberrypi.org/documentation/installation/
- Tested on Raspberry Pi OS 12 (Bookworm)

### 2. Pi-hole Installed and Working

Pi-hole must be installed and actively working as your network's DNS server before adding this display:

- ✅ Pi-hole is blocking ads and tracking queries on your network
- ✅ Admin interface is accessible at `http://your-pi-ip/admin`
- ✅ Dashboard shows statistics and blocked queries

**Don't have Pi-hole yet?**
- Official installation: https://docs.pi-hole.net/main/basic-install/
- Quick install: `curl -sSL https://install.pi-hole.net | bash`
- Complete the setup wizard and verify it's working before continuing

### 3. System Updated

Update your system before installing display hardware:

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### ✅ Phase 1 Checkpoint

Before continuing to Phase 2, verify:
- [ ] Your Raspberry Pi boots successfully
- [ ] You can SSH into your Pi or access the console
- [ ] Pi-hole web interface is accessible
- [ ] Pi-hole is actively blocking ads on your network

**All set?** Continue to Phase 2: Hardware Setup

---

## Phase 2: Hardware Setup

Now that Pi-hole is running, add the physical display hardware.

### Required Hardware

You'll need the following display components:

* **Adafruit PiTFT Plus 320x240 2.8" TFT**
  - Product link: https://www.adafruit.com/product/2423

* **Faceplate and Buttons Pack for 2.8" PiTFTs**
  - Product link: https://www.adafruit.com/product/2807

* **Case** (optional, but recommended)
  - Example: Pi Model B+ / Pi 2 / Pi 3 Case for 2.8" PiTFT
  - Product link: https://www.adafruit.com/product/3062

<img src="doc/img/PiTFT_buttons_parts.jpg" style=" width:480px; " >

### Physical Installation

1. **Power off your Raspberry Pi**:
   ```bash
   sudo shutdown -h now
   ```
   Wait for the Pi to fully power down before proceeding.

2. **Attach the PiTFT display**:
   - Connect the PiTFT to the 40-pin GPIO connector on your Raspberry Pi
   - Press firmly but gently to ensure all pins are seated

<img src="doc/img/PiTFT_plugin.jpg" style=" width:480px; " >

3. **Install the faceplate and buttons** (if using)
   - Attach the button pack to the side of the display
   - Install the faceplate over the display

### Install Display Drivers

The PiTFT display requires special drivers from Adafruit.

1. **Install prerequisite packages**:
   ```bash
   sudo pip3 install --upgrade adafruit-python-shell click==7.0
   ```

2. **Download Adafruit installer scripts**:
   ```bash
   cd ~
   git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
   cd Raspberry-Pi-Installer-Scripts
   ```

3. **Run the PiTFT installer**:

   For PiTFT 2.8" Capacitive (most common):
   ```bash
   sudo python3 adafruit-pitft.py --display=28c --rotation=90 --install-type=console
   ```

   For other display types, see: https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/easy-install-2

4. **Reboot when prompted**:
   ```bash
   sudo reboot
   ```

After reboot, the PiTFT display should show the console. You should see the normal Raspberry Pi boot messages on the small screen.

### Configure Console Display

Now optimize the console for the small display.

1. **Configure console font mapping**:

   Edit `/boot/cmdline.txt`:
   ```bash
   sudo nano /boot/cmdline.txt
   ```

   Add to the end of the line (after "rootwait"):
   ```
   fbcon=map:10 fbcon=font:VGA8x8
   ```

   The complete line should look similar to:
   ```
   console=serial0,115200 console=tty1 root=PARTUUID=XXXXXXXX-XX rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait fbcon=map:10 fbcon=font:VGA8x8
   ```

   **Note:** Don't change your existing PARTUUID value

   Save and exit (Ctrl+X, Y, Enter)

2. **Improve console font for readability**:

   Run the console setup utility:
   ```bash
   sudo dpkg-reconfigure console-setup
   ```

   Select these options:
   - **Encoding**: UTF-8
   - **Character set**: Guess optimal character set
   - **Font**: Terminus
   - **Font size**: 6x12 (framebuffer only)

3. **Reboot to apply changes**:
   ```bash
   sudo reboot
   ```

After reboot, the console should be more readable on the small display.

### Enable Auto-Login

> **⚠️ CRITICAL REQUIREMENT**: The display controller requires console auto-login to start automatically on boot. Without this, the application will not start.

Configure auto-login using raspi-config:

```bash
sudo raspi-config
```

Navigate through these menus:
- Select "1 System Options"
- Select "S5 Boot / Auto Login"
- Select "B2 Console Autologin" (Text console, automatically logged in as 'pi' user)
- Select Finish

When prompted to reboot, select "No" (we'll reboot after Phase 3)

**Verify auto-login is configured**:
```bash
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf
```

You should see a line containing `--autologin pi`

### ✅ Phase 2 Checkpoint

Before continuing to Phase 3, verify:
- [ ] PiTFT display shows the console
- [ ] Console font is readable on the small screen
- [ ] Auto-login is enabled (verified with the cat command above)

**All set?** Continue to Phase 3: Application Installation

---

## Phase 3: Application Installation

Now install the display controller software that will run PADD and handle button inputs.

### Install System Dependencies

1. **Install required system packages**:
   ```bash
   sudo apt install python3-pip git tmux pigpio
   ```

2. **Install yq** (YAML configuration parser):

   For most Raspberry Pi installations (32-bit OS):
   ```bash
   sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_arm -O /usr/bin/yq
   sudo chmod +x /usr/bin/yq
   ```

   If you're using 64-bit Raspberry Pi OS:
   ```bash
   sudo wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_arm64 -O /usr/bin/yq
   sudo chmod +x /usr/bin/yq
   ```

### Clone the Repository

Clone this repository with the PADD submodule:

```bash
cd ~
git clone --recurse-submodules https://github.com/andersix/pihole_display.git
```

If you already cloned without submodules, initialize them:
```bash
cd ~/pihole_display
git submodule update --init --recursive
```

**About PADD:** This project includes PADD (Pi-hole Admin Display Dashboard) as a git submodule. PADD is developed and maintained by the Pi-hole project at https://github.com/pi-hole/PADD. It's configured by default in `config/config.yaml` to run from the `PADD/` subdirectory.

### Install Python Dependencies

Install the required Python packages:

```bash
cd ~/pihole_display
sudo pip3 install -r requirements.txt
```

This installs: gpiozero, PyYAML, pigpio, and setuptools.

### Configure Pi-hole Authentication

PADD requires permission to access Pi-hole data. Add your user to the pihole group:

```bash
sudo usermod -G pihole pi
```

For more authentication options, see: https://github.com/pi-hole/PADD?tab=readme-ov-file#authentication

### Configure pigpio Service

Enable Remote GPIO and start the pigpio daemon:

1. **Enable Remote GPIO**:
   ```bash
   sudo raspi-config
   ```
   - Select "3 Interface Options"
   - Select "P8 Remote GPIO"
   - Select "Yes" to enable
   - Select Finish

2. **Enable and start pigpiod service**:
   ```bash
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod
   ```

3. **Verify it's running**:
   ```bash
   sudo systemctl status pigpiod
   ```

   You should see "Active: active (running)"

**Note:** The pigpiod service only listens locally by default (secure).

### Configure Auto-Start

The display controller needs to start automatically when the Pi boots.

Edit `~/.bashrc` and add this code **at the very top** of the file:

```bash
nano ~/.bashrc
```

Add these lines at the top:

```bash
# Run PiHole display controller
if [ "$TERM" == "linux" ] ; then
  if [ -f /home/pi/pihole_display/scripts/start_display.sh ]; then
      /home/pi/pihole_display/scripts/start_display.sh
      return 0
  fi
fi
```

Save and exit (Ctrl+X, Y, Enter)

**What this does:**
- Automatically runs when you log in on the console (not SSH)
- Creates a tmux session with two windows
- Starts PADD in the first window (displays Pi-hole statistics)
- Starts the button controller in the second window
- Logs startup activity to `log/startup.log`

### Final Reboot

Reboot your Pi to start the display controller:

```bash
sudo reboot
```

**What to expect:**
- The PiTFT display will show boot messages
- After ~30 seconds, PADD will appear showing Pi-hole statistics
- Buttons will be active and ready to use

### ✅ Phase 3 Complete!

Verify everything is working:
- [ ] PiTFT display shows PADD with Pi-hole statistics
- [ ] Button 1 dims the display when pressed
- [ ] Holding Button 1 for 2 seconds shows the Pi-hole Update Menu

**Success!** Your Pi-hole display controller is now running.

If you encounter any issues, see the Troubleshooting section below.

---

# Configuration

Most users won't need to change anything, but all settings can be customized if needed.

## Configuration File

All settings are in: `~/pihole_display/config/config.yaml`

Common settings you might want to adjust:

**Brightness Levels:**
- Default: 8 levels from 100% down to 0% (off)
- Edit the `display.backlight.brightness_levels` array
- Values are 0.0-1.0 (0.0 = off, 1.0 = full brightness)
- Gamma correction: `display.backlight.gamma` (default: 1.8 for perceptual linearity)

**Timing:**
- Menu timeout: `timing.confirmation_timeout` (default: 30 seconds)
- Feedback delay: `timing.feedback_delay` (default: 3 seconds)

**Paths:**
- Only change if you installed PADD or this application in a non-default location
- Update `paths.padd_dir` and `paths.padd_script` if using custom PADD location

**After making changes**, restart the application (see below).

## Restarting After Changes

If you make configuration changes or want to restart the application:

1. **Kill the existing tmux session**:
   ```bash
   tmux kill-session -t display
   ```

2. **Restart the application**:
   ```bash
   /home/pi/pihole_display/scripts/start_display.sh
   ```

The display should show PADD within a few seconds.

**Alternative - Reboot the Pi:**

Using command line:
```bash
sudo reboot
```

Or using the buttons:
- Hold Button 2 for 2 seconds (System Control Menu)
- Press Button 3 (Restart System)

---

# Troubleshooting

## Common Issues

### Display Not Showing PADD

**Check if the tmux session is running:**
```bash
tmux list-sessions
```

You should see a session named "display". If not:

1. **Check startup logs:**
   ```bash
   cat ~/pihole_display/log/startup.log
   ```

2. **Verify PADD submodule is initialized:**
   ```bash
   ls ~/pihole_display/PADD/padd.sh
   ```
   If file doesn't exist, initialize submodules:
   ```bash
   cd ~/pihole_display
   git submodule update --init --recursive
   ```

3. **Manually start the session:**
   ```bash
   /home/pi/pihole_display/scripts/start_display.sh
   ```

### Buttons Not Responding

1. **Check if Python process is running:**
   ```bash
   pgrep -f "main.py"
   ```
   Should return a process ID. If not, the controller isn't running.

2. **Verify pigpiod is running:**
   ```bash
   sudo systemctl status pigpiod
   ```
   Should show "Active: active (running)". If not:
   ```bash
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod
   ```

3. **Check application logs for errors:**
   ```bash
   tail -f ~/pihole_display/log/pihole_display.log
   ```

### Application Won't Start on Boot

1. **Verify auto-login is enabled:**
   ```bash
   cat /etc/systemd/system/getty@tty1.service.d/autologin.conf
   ```
   Should contain `--autologin pi`

2. **Check .bashrc has startup code:**
   ```bash
   head -10 ~/.bashrc
   ```
   The startup code should be at the very top of the file.

3. **Verify file paths are correct:**
   ```bash
   ls -la /home/pi/pihole_display/scripts/start_display.sh
   ```

## Viewing Logs

### Startup Logs
Shows tmux session creation and initialization:
```bash
cat ~/pihole_display/log/startup.log
```

### Application Logs
Shows runtime activity, button presses, and errors:
```bash
tail -f ~/pihole_display/log/pihole_display.log
```

### Live Monitoring
Attach to the tmux session to see what's happening:
```bash
tmux attach -t display
```

**Tmux keyboard shortcuts:**
- `Ctrl+b` then `w` - List and switch between windows
- `Ctrl+b` then `0` - Switch to PADD window
- `Ctrl+b` then `1` - Switch to control window
- `Ctrl+b` then `d` - Detach without stopping the session

---

# Updating the Application

When there are updates to this project:

```bash
cd ~/pihole_display
git pull
sudo reboot
```

The reboot will automatically start the updated application via the `.bashrc` startup script.

**Note:** PADD updates are handled via Button 4 in the Pi-hole Update Menu (hold Button 1 for 2 seconds, then press Button 4). The button update runs `git pull` in the PADD submodule directory to fetch the latest version from the Pi-hole project repository.
