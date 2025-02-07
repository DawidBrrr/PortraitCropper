import customtkinter as ctk

#ProgressPopup
class ProgressBarPopup(ctk.CTkToplevel):
    def __init__(self,master):
        super().__init__(master)
        self.geometry("400x200")
        self.title("Kadrowanie")


        self.attributes("-topmost", True) # popup stay on top
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Disable the close button

        self.text_font = ctk.CTkFont(family="Arial", size=18)
        self.grid_columnconfigure((0, 1), weight=1)

        # progressbar
        self.crop_progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate")
        self.crop_progress_bar.grid(row=0, column=0, padx=20, pady=20, sticky="sew", columnspan=2)
        self.crop_progress_bar.start()
        # napis
        self.cropping_label = ctk.CTkLabel(self, text="Kadrowanie", fg_color="gray16", corner_radius=6,
                                           text_color="white", font=self.text_font)
        self.cropping_label.grid(row=1, column=0, padx=20, pady=20, sticky="sew", columnspan=2)

    def on_closing(self):
        # Prevent the window from being closed manually
        pass