import customtkinter as ctk
import os
import shutil
from Frames import InputsFrame
from Frames import PathFrame
from Frames import AttributeParsingFrame
from Frames import PreviewFrame
from Cropper import CropperClass
import cv2
from PIL import Image
from tkinter import messagebox



ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

global_dpi = None


#Aplikacja
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Kaidr")
        self.geometry("600x400")
        self.after(0, lambda: self.state('zoomed'))#whole screen cover

        # Create main scrollable container
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_columnconfigure((0,2), weight=1)
        
        # Configure main window grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.title_font = ctk.CTkFont(family="Oswald",size = 50,weight = "bold")
        self.text_font = ctk.CTkFont(family = "Arial",size = 18)

        # Move all existing frames to main_container
        self.toolbar_frame = ctk.CTkFrame(self.main_container)
        self.toolbar_frame.grid_columnconfigure((0,2),weight=1)
        self.toolbar_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew", columnspan=3)

        self.input_data_frame = InputsFrame(self.main_container)
        self.input_data_frame.grid(row=3, column=2, padx=20, pady=20, sticky="nse")

        self.flipping_frame = ctk.CTkFrame(self.main_container)
        self.flipping_frame.grid_columnconfigure((0,1), weight=1)
        self.flipping_frame.grid(row=4, column=2, padx=20, pady=20, sticky="nse")

        self.preview_frame = PreviewFrame(self.main_container, self.input_data_frame)
        self.preview_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew", rowspan=5, columnspan=2)

        self.path_frame = PathFrame(self.main_container, self.preview_frame)
        self.path_frame.grid(row=2, column=2, padx=20, pady=20, sticky="nse")

        self.attribute_parsing_frame = AttributeParsingFrame(self.main_container, self.path_frame)
        self.attribute_parsing_frame.grid(row=5, column=2, padx=20, pady=20, sticky="nse")

        # Move buttons to toolbar_frame
        self.crop_button = ctk.CTkButton(self.toolbar_frame, text="Skadruj", command=self.CropButton)
        self.crop_button.grid(row=0, column=2, padx=20, pady=20, sticky="se")

        self.scaling_options = ["50%","60%","75%","100%","150%","200%"]
        self.scaling_var = ctk.StringVar(value="100%") #100% scaling by default
        self.scale_dropdown = ctk.CTkOptionMenu(self.toolbar_frame,values=self.scaling_options, command = self.change_scaling,variable=self.scaling_var)
        self.scale_dropdown.grid(row = 0,column = 2,padx=20,pady=20,sticky="s")

        # Move rotation buttons to flipping_frame
        self.rotate_images_button = ctk.CTkButton(self.flipping_frame, text="Obróć", command=self.rotate_images)
        self.rotate_images_button.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.flip_images_button = ctk.CTkButton(self.flipping_frame, text="Lustrzane", command=self.flip_images)
        self.flip_images_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
    
        #Bind the close event to cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    #Exiting Fullscreen
    def exit_fullscreen(self, event=None):
        self.attributes('-fullscreen', False)

    def CropButton(self):
        #Make Dpi global var
        global global_dpi
        global_dpi = self.input_data_frame.dpi_entry.get()
        #check if crucial arguments are provided
        if not self.path_frame.input_entry.get():
            messagebox.showwarning("Nie można kontynuować","Wprowadź folder wejściowy")
        elif not self.path_frame.output_entry.get():
            messagebox.showwarning("Nie można kontynuować", "Wprowadź folder wyjściowy")

        else:
            cropper = CropperClass(input_path=self.path_frame.input_entry.get(),
                                   output_path=self.path_frame.output_entry.get(),
                                   debug_output="InternalData/Debug",
                                   preview_output_res=256,
                                   preview_debug_max_res=512,
                                   res_x=int(self.input_data_frame.get_x_in_px(self.path_frame.input_entry.get())),
                                   res_y=int(self.input_data_frame.get_y_in_px(self.path_frame.input_entry.get())),
                                   show_preview=False,
                                   croptype=2,
                                   top_margin_value=float(self.input_data_frame.top_margin_entry.get()),
                                   bottom_margin_value=float(self.input_data_frame.bottom_margin_entry.get()))                                                                   
            cropper.CropFaces(self)

    def on_closing(self):
        self.cleanup_placeholder_folders()
        self.destroy()

    def cleanup_placeholder_folders(self):
        #Defining Paths
        internal_data_path = "InternalData"
        edited_images_placeholder_path = os.path.join(internal_data_path,"Edited IMAGE Placeholder")
        images_placeholder_path = os.path.join(internal_data_path,"IMAGE Placeholder")
        debug_placeholder_path = os.path.join(internal_data_path,"Debug")

        #cleanup folders
        for folder in [edited_images_placeholder_path,images_placeholder_path,debug_placeholder_path]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                os.makedirs(folder)#recreating empty folders

    #Rotate images 90 degrees
    def rotate_images(self):
        if self.path_frame.input_entry.get() == None:
            print("Select an input path")
            pass
        else:
            input_folder = self.path_frame.input_entry.get()
            # Iterate over all files in the input folder
            for filename in os.listdir(input_folder):
                # Construct the full file path
                file_path = os.path.join(input_folder, filename)

                # Check if the file is an image (simple check based on file extension)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    # Read the image
                    image = cv2.imread(file_path)

                    # Check if image is loaded properly
                    if image is None:
                        print(f"Warning: Could not open or find the image {filename}. Skipping.")
                        continue

                    # Flip the image
                    rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

                    # Save the flipped image, replacing the original image
                    cv2.imwrite(file_path, rotated_image)
                    self.path_frame.display_images(input_folder)
                    self.preview_frame.set_folder_path(self.path_frame.input_entry.get())
                    self.preview_frame.first_image()


    #Flip images / mirror image
    def flip_images(self):
        if self.path_frame.input_entry.get() == None:
            print("Select an input path")
            pass
        else:
            input_folder = self.path_frame.input_entry.get()

            # Iterate over all files in the input folder
            for filename in os.listdir(input_folder):
                # Construct the full file path
                file_path = os.path.join(input_folder, filename)

                # Check if the file is an image (simple check based on file extension)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    # Read the image
                    image = cv2.imread(file_path)

                    # Check if image is loaded properly
                    if image is None:
                        print(f"Warning: Could not open or find the image {filename}. Skipping.")
                        continue

                    # Flip the image
                    flipped_image = cv2.flip(image, 1)#0 for x-axis 1 for y-axis -1 for both

                    # Save the flipped image, replacing the original image
                    cv2.imwrite(file_path, flipped_image)
                    self.path_frame.display_images(input_folder)
                    self.preview_frame.set_folder_path(self.path_frame.input_entry.get())
                    self.preview_frame.first_image()
    def change_scaling(self,choice):
        scaling_values = {
            "50%": 0.5,
            "60%": 0.6,
            "75%": 0.75,
            "100%": 1,
            "150%": 1.5,
            "200%": 2
        }
        selected_scaling = scaling_values.get(choice,1.0)
        ctk.set_widget_scaling(selected_scaling)

