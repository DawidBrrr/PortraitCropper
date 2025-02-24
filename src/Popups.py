import customtkinter as ctk

class ProgressBarPopup(ctk.CTkToplevel):
    def __init__(self, master, title, label_text):
        super().__init__(master)
        self.geometry("400x200")
        self.title(title)
        
        self.attributes("-topmost", True)  # Popup stays on top
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # Disable the close button

        self.text_font = ctk.CTkFont(family="Arial", size=18)
        self.grid_columnconfigure((0, 1), weight=1)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate")
        self.progress_bar.grid(row=0, column=0, padx=20, pady=20, sticky="sew", columnspan=2)
        self.progress_bar.start()

        # Label
        self.label = ctk.CTkLabel(self, text=label_text, fg_color="gray16", corner_radius=6,
                                  text_color="white", font=self.text_font)
        self.label.grid(row=1, column=0, padx=20, pady=20, sticky="sew", columnspan=2)

    def on_closing(self):
        # Prevent the window from being closed manually
        pass

# Derived classes
class CroppingProgressBarPopup(ProgressBarPopup):
    def __init__(self, master):
        super().__init__(master, "Kadrowanie", "Kadrowanie")

class RotateProgressBarPopup(ProgressBarPopup):
    def __init__(self, master):
        super().__init__(master, "Obracanie", "Obracanie")

class FlipProgressBarPopup(ProgressBarPopup):
    def __init__(self, master):
        super().__init__(master, "Przerzucanie", "Przerzucanie")
