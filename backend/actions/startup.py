import os
from backend.config import PROJECT_ROOT

def add_to_startup() -> str:
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    if not startup_dir:
        return "Could not locate the Windows startup directory."
        
    bat_file = os.path.join(startup_dir, "ViruAssistant.bat")
    
    try:
        with open(bat_file, "w") as f:
            f.write("@echo off\n")
            f.write(f"cd /d \"{PROJECT_ROOT}\"\n")
            # Run using pythonw.exe so no black console window appears
            f.write("start \"\" /min .\\.venv\\Scripts\\pythonw.exe -m backend.tray\n")
        return "Ghost Mode successfully injected into Windows Startup!"
    except Exception as e:
        return f"Failed to add to startup: {e}"
        
def remove_from_startup() -> str:
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    bat_file = os.path.join(startup_dir, "ViruAssistant.bat")
    
    if os.path.exists(bat_file):
        try:
            os.remove(bat_file)
            return "Ghost Mode removed from Windows Startup."
        except Exception as e:
            return f"Failed to remove from startup: {e}"
    return "Ghost Mode was not enabled on startup."
