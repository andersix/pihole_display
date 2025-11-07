# Pi-hole Display Controller

Physical display and button controls for your Pi-hole installation.

<img src="doc/img/PiTFT_padd.jpg" style=" width:480px; " >

---

## What is This?

The **Pi-hole Display Controller** adds a 2.8" LCD display and button controls to your Raspberry Pi running Pi-hole. It displays real-time Pi-hole statistics via PADD (Pi-hole Admin Display Dashboard) and provides physical buttons for managing your Pi-hole and system without needing SSH or a keyboard.

This is an enhancement to an existing, working Pi-hole setup. You should have Pi-hole installed and functioning on a Raspberry Pi before adding this display controller.

---

## Features

✨ **Real-time Statistics Display**
- Shows Pi-hole stats, queries blocked, gravity database info
- Displays network information and system status
- Updates automatically via PADD dashboard
- Adjustable display brightness (8 levels)

🎮 **Physical Button Controls**
- Dim display with single button press
- Update Pi-hole gravity database
- Update Pi-hole core software
- Update PADD dashboard
- Update Raspberry Pi OS and packages
- Reboot or shutdown system safely

🚀 **Automatic Startup**
- Starts automatically on boot
- No SSH or keyboard required once configured
- Runs in background via tmux sessions

🔧 **Highly Configurable**
- Centralized YAML configuration
- Customizable display brightness levels with gamma correction
- Adjustable menu timeouts
- Configurable paths for custom installations

---

## Hardware Requirements

- **Raspberry Pi**: 3B, 3B+, or 4 (RPi 5 not supported)
- **Display**: Adafruit PiTFT Plus 320x240 2.8" TFT ([link](https://www.adafruit.com/product/2423))
- **Buttons**: Faceplate and Buttons Pack for 2.8" PiTFTs ([link](https://www.adafruit.com/product/2807))
- **Case**: Optional but recommended ([example](https://www.adafruit.com/product/3062))

<img src="doc/img/PiTFT_buttons_parts.jpg" style=" width:480px; " >

---

## Documentation

📖 **[Installation Guide](INSTALL.md)** - Complete setup instructions from start to finish

🎮 **[User Guide](USER_GUIDE.md)** - How to use the buttons and control your Pi-hole

---

## Quick Overview

### Button Layout

```
 ┌─────────────────────────┌─────────────┐
 │ PI-HOLE =============== │  Button 1   │ ← Brightness / Pi-hole Menu
 │                         ├─────────────┤
 │ STATS ================= │  Button 2   │ ← System Menu
 │                         ├─────────────┤
 │ NETWORK =============== │  Button 3   │ ← Menu Option 1
 │                         ├─────────────┤
 │ SYSTEM ================ │  Button 4   │ ← Menu Option 2
 └─────────────────────────└─────────────┘
```

### Normal Mode (PADD Display)
- **Button 1 Press**: Cycle brightness levels, from full to off
- **Button 1 Hold (2s)**: Open Pi-hole Update Menu
- **Button 2 Hold (2s)**: Open System Control Menu

### Pi-hole Update Menu
- **Button 2**: Update Gravity (blocklists)
- **Button 3**: Update Pi-hole core
- **Button 4**: Update PADD dashboard

### System Control Menu
- **Button 2**: Update Raspberry Pi OS
- **Button 3**: Reboot system
- **Button 4**: Shutdown system

See the **[User Guide](USER_GUIDE.md)** for detailed instructions.

---

## Software Components

This project uses:
- **Python 3** - Application logic and hardware control
- **PADD** - Pi-hole Admin Display Dashboard (included as submodule from [pi-hole/PADD](https://github.com/pi-hole/PADD))
- **tmux** - Terminal multiplexer for managing display and control windows
- **pigpio** - Hardware PWM control for display backlight
- **gpiozero** - GPIO button interface

---

## Getting Started

Ready to install? Head over to the **[Installation Guide](INSTALL.md)** for complete setup instructions.

The installation process has three phases:
1. **Foundation** - Ensure Raspberry Pi and Pi-hole are working
2. **Hardware** - Install and configure the PiTFT display
3. **Application** - Install the display controller software

Estimated time: 1-2 hours for first-time installation

---

## Screenshots

<img src="doc/img/PiTFT_padd.jpg" style=" width:480px; " >
*PADD displaying Pi-hole statistics*

<img src="doc/img/PiTFT_phupdate.jpg" style=" width:480px; " >
*Pi-hole Update Menu*

<img src="doc/img/PiTFT_sysupdate.jpg" style=" width:480px; " >
*System Control Menu*

---

## Contributing

Contributions are welcome! Here's how you can help:

- 🐛 **Report bugs** - Open an issue describing the problem
- 💡 **Suggest features** - Share your ideas for improvements
- 🔧 **Submit pull requests** - Fix bugs or add features
- 📖 **Improve documentation** - Help make the docs clearer

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Components

- **Pi-hole** - Licensed under EUPL v1.2 (https://github.com/pi-hole/pi-hole)
- **PADD** - Part of the Pi-hole project (https://github.com/pi-hole/PADD)

---

## Support

- 📚 **Documentation**: [Installation Guide](INSTALL.md) | [User Guide](USER_GUIDE.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/andersix/pihole_display/issues)
- 💬 **Discussions**: Open a GitHub issue for questions

---

## Acknowledgments

- **Pi-hole Team** - For the amazing ad-blocking DNS server and PADD dashboard
- **Adafruit** - For the PiTFT display hardware and driver software
- **Community Contributors** - For feedback, bug reports, and improvements
