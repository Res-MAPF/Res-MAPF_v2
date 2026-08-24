from src.view.controller import MainGUIController
import customtkinter as ctk
from pathlib import Path
import tkinter
import os
import sys

# Salva l'original excepthook
_original_excepthook = sys.excepthook

def suppress_customtkinter_errors(exc_type, exc_value, exc_traceback):
    """Suppress specific CustomTkinter errors that don't affect functionality"""
    # Suppress AttributeError from CustomTkinter scrollable frame mouse wheel handler
    if (exc_type is AttributeError and 
        "'str' object has no attribute 'master'" in str(exc_value)):
        return
    # Handle all other errors normally
    _original_excepthook(exc_type, exc_value, exc_traceback)

# Monkey-patch Tkinter's exception handling per i callback
def setup_tkinter_exception_handler():
    """Patch Tkinter's report_callback_exception to suppress known non-critical errors"""
    original_report = tkinter.Tk.report_callback_exception
    
    def custom_report_callback(self, exc_type, exc_value, exc_traceback):
        # Suppress the specific CustomTkinter mouse wheel error
        if (exc_type is AttributeError and 
            "'str' object has no attribute 'master'" in str(exc_value)):
            return
        # Call original handler for all other errors
        return original_report(self, exc_type, exc_value, exc_traceback)
    
    tkinter.Tk.report_callback_exception = custom_report_callback

# Setup handlers before creating GUI
setup_tkinter_exception_handler()
sys.excepthook = suppress_customtkinter_errors

if __name__ == '__main__':
    theme_path = str(Path("themes/midnight.json"))
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme(theme_path)
    ctk.set_window_scaling(1.0)
    ctk.set_widget_scaling(1.0)

    app = MainGUIController()
    app.run()