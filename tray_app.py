import pystray
from PIL import Image, ImageDraw
import _thread

def create_image():
    """Generates a simple 64x64 green icon for the system tray."""
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), color=(20, 20, 20))
    dc = ImageDraw.Draw(image)
    # Draw a green square to signify "Safe/Monitoring"
    dc.rectangle((16, 16, 48, 48), fill=(0, 255, 128))
    return image

class SystemTrayApp:
    def __init__(self, session_state, verification_thread):
        self.session_state = session_state
        self.verification_thread = verification_thread
        self.icon = None

    def on_pause_clicked(self, icon, item):
        self.verification_thread.pause_monitoring()
        icon.title = "Face Auth [PAUSED]"
        icon.update_menu()

    def on_resume_clicked(self, icon, item):
        self.verification_thread.resume_monitoring()
        icon.title = "Face Auth Active"
        icon.update_menu()

    def on_logout_clicked(self, icon, item):
        self.verification_thread.stop()
        icon.stop() # Stops the pystray blocking loop
        _thread.interrupt_main() # Safely return to the main login prompt

    def get_menu(self):
        # Dynamic visibility handlers for the context menu
        def is_paused(item):
            return self.verification_thread.is_paused

        def is_running(item):
            return not self.verification_thread.is_paused

        return pystray.Menu(
            pystray.MenuItem(f"Status: Logged in as {self.session_state.name} ({self.session_state.roll_number})", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pause Monitoring", self.on_pause_clicked, visible=is_running),
            pystray.MenuItem("Resume Monitoring", self.on_resume_clicked, visible=is_paused),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Logout & Exit", self.on_logout_clicked)
        )

    def run(self):
        """Starts the blocking system tray application."""
        self.icon = pystray.Icon("FaceAuth", create_image(), "Face Auth Active", menu=self.get_menu())
        self.icon.run()
