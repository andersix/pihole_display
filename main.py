# vim:tabstop=4:softtabstop=4:shiftwidth=4:textwidth=79:expandtab:autoindent:smartindent:fileformat=unix:

import signal
import logging
from src.utils.config import Config
from src.models import ButtonConfig
from src.controllers.button_manager import ButtonManager
from src.display.manager import DisplayManager

logger = logging.getLogger('DisplayController')

def main():
    """PiHole Display Main"""
    try:
        # Initialize configuration
        config = Config()

        # Initialize display manager
        display = DisplayManager()

        # Create button manager with display
        manager = ButtonManager(display)

        # Check PADD session exists
        if not display.check_padd():
            logger.error("Failed to find PADD display session")
            return

        def button1_held(hold_time: float):
            """Handle button 1 hold - system control selection"""
            if not manager.system._waiting_for_confirmation and not manager.pihole._waiting_for_confirmation:
                logger.debug("Selected System Menu")
                manager.system.handle_button1_held(hold_time)

        def button2_held(hold_time: float):
            """Handle button 2 hold - update selection"""
            if not manager.system._waiting_for_confirmation and not manager.pihole._waiting_for_confirmation:
                logger.debug("Selected Pi-Hole Menu")
                manager.pihole.handle_button2_held(hold_time)

        def button1_pressed():
            """Handle button 1 press - cycle brightness"""
            if manager.pihole._waiting_for_confirmation or manager.system._waiting_for_confirmation:
                logger.debug("Button 1 pressed - cancelling confirmation")
                manager.cancel_confirmation()
                return
            try:
                manager.backlight.step_brightness()
                current_brightness = manager.backlight.get_brightness_percentage()
                logger.info(f"Brightness changed to {current_brightness}%")
            except Exception as e:
                logger.error(f"Error handling button 1 press: {str(e)}")

        def button2_pressed():
            """Handle button 2 press - cancelling if in confirmation"""
            if manager.system._waiting_for_confirmation:
                logger.debug("In system menu - confirming system update")
                manager.system.handle_button2_press()
            elif manager.pihole._waiting_for_confirmation:
                logger.debug("In Pi-hole menu - confirming Gravity update")
                manager.pihole.handle_button2_press()
#            if manager.pihole._waiting_for_confirmation or manager.system._waiting_for_confirmation:
#                logger.debug("Button 2 pressed - cancelling confirmation")
#                manager.cancel_confirmation()
#                return

        def button3_pressed():
            """
            Handle button 3 press
            - In Pi-hole menu: Confirms Pi-hole update
            - In system menu: Confirms system restart
            """
            if manager.system._waiting_for_confirmation:
                logger.debug("In system menu - confirming restart")
                manager.system.handle_button3_press()
            elif manager.pihole._waiting_for_confirmation:
                logger.debug("In Pi-hole menu - confirming Pi-hole update")
                manager.pihole.handle_button3_press()

        def button4_pressed():
            """
            Handle button 4 press
            - In Pi-hole menu: Confirms PADD update
            - In system menu: Confirms system shutdown
            """
            if manager.system._waiting_for_confirmation:
                logger.debug("In system menu - confirming shutdown")
                manager.system.handle_button4_press()
            elif manager.pihole._waiting_for_confirmation:
                logger.debug("In Pi-hole menu - confirming PADD update")
                manager.pihole.handle_button4_press()

        # Get button configurations from config
        button_configs = config.buttons

        # Configure and add buttons
        buttons_config = [
            (ButtonConfig(**button_configs['1']), button1_pressed, button1_held),
            (ButtonConfig(**button_configs['2']), button2_pressed, button2_held),
            (ButtonConfig(**button_configs['3']), button3_pressed, None),
            (ButtonConfig(**button_configs['4']), button4_pressed, None),
        ]

        # Add all buttons to the manager
        for config, callback, hold_callback in buttons_config:
            manager.add_button(
                config=config,
                callback=callback,
                hold_callback=hold_callback
            )

        logger.info("PiHole Display started successfully")

        # Set up signal handlers
        def cleanup_handler(signum, frame):
            """Handle cleanup on termination signals"""
            logger.info(f"Received signal {signum}, cleaning up")
            if 'manager' in locals():
                manager.cleanup()
            exit(0)

        signal.signal(signal.SIGTERM, cleanup_handler)
        signal.signal(signal.SIGINT, cleanup_handler)

        # Keep this sumbitch runnin...
        signal.pause()

    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        raise
    finally:
        if 'manager' in locals():
            manager.cleanup()

if __name__ == "__main__":
    main()

