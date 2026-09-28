import os
import sys
import winshell
from win32com.client import Dispatch

# Path to the packaged executable - in project's dist folder
exe_path = r"E:\playground\Projects\music-player\dist\MusicPlayer\MusicPlayer.exe"
icon_path = r"E:\playground\Projects\music-player\assets\MusicPlayer.ico"

# Desktop path
desktop = winshell.desktop()
shortcut_path = os.path.join(desktop, "MusicPlayer.lnk")

# Create shortcut
shell = Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.Targetpath = exe_path
shortcut.WorkingDirectory = os.path.dirname(exe_path)
shortcut.IconLocation = icon_path
shortcut.Description = "MusicPlayer - Desktop Music Player"
shortcut.save()

print(f"Created shortcut at: {shortcut_path}")
print(f"Target: {exe_path}")
print(f"Icon: {icon_path}")
print(f"Working Directory: {os.path.dirname(exe_path)}")