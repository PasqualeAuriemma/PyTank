from esp32_app import PyTankApp
import machine
import time
import gc

def main():
    """
    Main application entry point for the PyTank project.
    """
    print("Starting PyTank Application...")
    
    try:
        # Initialize the main application
        # This encapsulates the logic previously found in main.py
        app = PyTankApp()
        
        # Main Loop
        app.run()
            
    except KeyboardInterrupt:
        print("Application stopped by user.")
    except Exception as e:
        print(f"Critical Error: {e}")
        # In a production environment, you might want to log this to a file on the SD card
        print("Restarting in 5 seconds...")
        time.sleep(5)
        machine.reset()

if __name__ == "__main__":
    main()
