import customtkinter as ctk
import os
import sys
import shutil
import logging
import threading
from datetime import datetime
from Frames import InputsFrame
from Frames import PathFrame
#from Frames import AttributeParsingFrame
from Frames import PreviewFrame
from Frames import OutputFileNameFrame
from Frames import TransformationsFrame
from Cropper import CropperClass
from Popups import RotateProgressBarPopup
from Popups import FlipProgressBarPopup
import cv2
from PIL import Image
from tkinter import messagebox

# Setup logging configuration 
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_filename = f'logs/portrait_cropper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # Configure root logger with detailed formatting
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s\n%(pathname)s:%(lineno)d')
    
    # File handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='w')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Capture stdout and stderr
    class StreamToLogger:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level
            self.linebuf = ''

        def write(self, buf):
            for line in buf.rstrip().splitlines():
                self.logger.log(self.level, line.rstrip())

        def flush(self):
            pass

    # Replace stdout and stderr with logging
    sys.stdout = StreamToLogger(root_logger, logging.INFO)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR)

    # Capture PIL warnings
    logging.getLogger('PIL').setLevel(logging.WARNING)

    # Handle uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook(exc_type, exc_value, exc_traceback)
            return
        
        logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

# Initialize logging if not already configured
if not logging.getLogger().handlers:
    setup_logging()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

global_dpi = None

#TODO add segmented button with presets at the top of the window
#TODO fix paths with polish characters
#TODO add a switch quick cropping => advanced cropping
#Aplikacja
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        logging.info("Initializing main application window")

        self.title("Kaidr")
        self.geometry("600x400")
        self.after(0, lambda: self.state('zoomed'))#whole screen cover

        # Configure main window grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)  # Preview section - 2/3
        self.grid_columnconfigure(1, weight=1)  # Controls section - 1/3

        # Preview container
        self.preview_container = ctk.CTkFrame(self)
        self.preview_container.grid(row=0, column=0, sticky="nsew", padx=(20,10), pady=20)
        self.preview_container.grid_rowconfigure(0, weight=1)
        self.preview_container.grid_columnconfigure(0, weight=1)

        #Controls container
        self.controls_container = ctk.CTkScrollableFrame(self)
        self.controls_container.grid(row=0, column=1, sticky="nsew", padx=(10,20), pady=20)
        self.controls_container.grid_columnconfigure(0, weight=1)

        self.title_font = ctk.CTkFont(family="Oswald", size=50, weight="bold")
        self.text_font = ctk.CTkFont(family="Arial", size=18)

        # Toolbar frame
        self.toolbar_frame = ctk.CTkFrame(self.controls_container, fg_color="gray15")
        self.toolbar_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.toolbar_frame.grid_columnconfigure((0,1,2,3), weight=1)

        #Path Frame
        self.path_frame = PathFrame(self.controls_container, None)
        self.path_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        #Transformations Frame
        self.transformations_frame = TransformationsFrame(self.controls_container)
        self.transformations_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        

        #Input Data Frame
        self.input_data_frame = InputsFrame(self.controls_container)
        self.input_data_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        #Output File Name Frame
        self.output_file_name_frame = OutputFileNameFrame(self.controls_container)
        self.output_file_name_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

        # Add preview frame to preview container
        self.preview_frame = PreviewFrame(self.preview_container, self.input_data_frame)
        self.preview_frame.grid(row=0, column=0, sticky="nsew")

        # Update path_frame with preview_frame reference
        self.path_frame.preview_frame = self.preview_frame

        # Add buttons to toolbar frame
        self.scaling_options = ["50%","60%","75%","100%","150%","200%"]
        self.scaling_var = ctk.StringVar(value="100%")
        self.scale_dropdown = ctk.CTkOptionMenu(self.toolbar_frame, 
                                              values=self.scaling_options, 
                                              command=self.change_scaling,
                                              variable=self.scaling_var)
        self.scale_dropdown.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        #button for rotating all images 90 degrees
        self.rotate_90_button = ctk.CTkButton(self.transformations_frame,
                                        text="Obróć o 90°",
                                        command=lambda: self.rotate_images(90))
        self.rotate_90_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        #button for rotating all images 180 degrees
        self.rotate_180_button = ctk.CTkButton(self.transformations_frame,
                                        text="Obróć o 180°",
                                        command=lambda: self.rotate_images(180))
        self.rotate_180_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        #button for rotating all images 270 degrees
        self.rotate_270_button = ctk.CTkButton(self.transformations_frame,
                                        text="Obróć o 270°",
                                        command=lambda: self.rotate_images(270))
        self.rotate_270_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        #button for flipping all images horizontally
        self.flip_button = ctk.CTkButton(self.transformations_frame,
                                        text="Lustrzane",
                                        command=self.flip_images)
        self.flip_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")        
        
        #cropping button
        self.crop_button = ctk.CTkButton(self.toolbar_frame, 
                                       text="Skadruj",
                                       font=("Arial", 16, "bold"),
                                       command=self.CropButton)
        self.crop_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

        # Bind the close event to cleanup
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
                                   res_x=int(self.input_data_frame.get_x_in_px(self.path_frame.input_entry.get())),
                                   res_y=int(self.input_data_frame.get_y_in_px(self.path_frame.input_entry.get())),                                                        
                                   top_margin_value=float(self.input_data_frame.top_margin_entry.get()),
                                   bottom_margin_value=float(self.input_data_frame.bottom_margin_entry.get()),
                                   left_right_margin_value=float(self.input_data_frame.left_right_margin_entry.get()),                                                                   
                                   naming_config = self.output_file_name_frame.get_naming_config())
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

    #Rotate images 
    def rotate_images(self,degrees):
        def rotate_process():
            try:
                if not self.path_frame.input_entry.get():
                    messagebox.showwarning("Nie można kontynuować","Wprowadź folder wejściowy")
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

                            # Choose rotation based on degrees
                            if degrees == 90:
                                rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                            elif degrees == 180:
                                rotated_image = cv2.rotate(image, cv2.ROTATE_180)
                            elif degrees == 270:
                                rotated_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

                            # Save the rotated image, replacing the original image
                            cv2.imwrite(file_path, rotated_image)                                                    
            except Exception as e:
                logging.exception(f"Error while rotating images: {e}")
            finally:
                self.after_idle(cleanup_progress_bar)    
        
        def cleanup_progress_bar():
            if hasattr(self, 'RotateProgressBarPopup'):
                try:
                    input_folder = self.path_frame.input_entry.get()
                    if input_folder:
                        self.path_frame.display_images(input_folder)
                        self.preview_frame.set_folder_path(input_folder)
                    self.RotateProgressBarPopup.destroy()
                    del self.RotateProgressBarPopup  # Bezpieczne usunięcie atrybutu
                except Exception as e:
                    logging.exception(f"Error in cleanup: {e}")       
        
        try:
            if hasattr(self, 'RotateProgressBarPopup'):
                self.RotateProgressBarPopup.destroy()
                del self.RotateProgressBarPopup  # Usuń referencję

            self.RotateProgressBarPopup = RotateProgressBarPopup(self)
            
            thread = threading.Thread(target=rotate_process, daemon=True)
            thread.start()
        except Exception as e:
            logging.exception(f"Multithreading Error: {e}")

        
                               


    #Flip images / mirror image
    def flip_images(self):
        def flip_process():
            try:
                if not self.path_frame.input_entry.get():
                    messagebox.showwarning("Nie można kontynuować","Wprowadź folder wejściowy")
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
                            flipped_image = cv2.flip(image, 1) # 1 for horizontal flip, 0 for vertical flip

                            # Save the flipped image, replacing the original image
                            cv2.imwrite(file_path, flipped_image)                                                    
            except Exception as e:
                logging.exception(f"Error while flipping images: {e}")
            finally:
                self.after_idle(cleanup_progress_bar)    
        
        def cleanup_progress_bar():
            if hasattr(self, 'FlipProgressBarPopup'):
                try:
                    input_folder = self.path_frame.input_entry.get()
                    if input_folder:
                        self.path_frame.display_images(input_folder)
                        self.preview_frame.set_folder_path(input_folder)
                    self.FlipProgressBarPopup.destroy()
                    del self.FlipProgressBarPopup  # Bezpieczne usunięcie atrybutu
                except Exception as e:
                    logging.exception(f"Error in cleanup: {e}")       
        
        try:
            if hasattr(self, 'FlipProgressBarPopup'):
                self.FlipProgressBarPopup.destroy()
                del self.FlipProgressBarPopup  # Usuń referencję

            self.FlipProgressBarPopup = FlipProgressBarPopup(self)
            
            thread = threading.Thread(target=flip_process, daemon=True)
            thread.start()
        except Exception as e:
            logging.exception(f"Multithreading Error: {e}")                    
    
    def change_scaling(self, choice):
        try:
            scaling_values = {
                "50%": 0.5,
                "60%": 0.6,
                "75%": 0.75,
                "100%": 1,
                "150%": 1.5,
                "200%": 2
            }
            selected_scaling = scaling_values.get(choice, 1.0)
            logging.info(f"Changing scaling to {choice} ({selected_scaling})")

            # Clear existing preview
            if hasattr(self.preview_frame, '_current_image'):
                self.preview_frame.current_image = None
            
            # Destroy and recreate preview frame
            self.preview_frame.grid_forget()
            self.preview_frame.destroy()
            
            # Apply scaling
            ctk.set_widget_scaling(selected_scaling)
            
            # Create new preview frame
            self.preview_frame = PreviewFrame(self.preview_container, self.input_data_frame)
            self.preview_frame.grid(row=0, column=0, sticky="nsew")
            
            # Update path frame reference
            self.path_frame.preview_frame = self.preview_frame
            
            # Update preview after short delay
            self.after(100, self._update_after_scaling)

        except Exception as e:
            logging.exception("Error while changing scaling:")

    def _update_after_scaling(self):
        try:
            if self.path_frame.input_entry.get():
                logging.info("Updating preview after scaling change")
                current_path = self.path_frame.input_entry.get()
                self.preview_frame.set_folder_path(current_path)
                self.preview_frame.preview_image()
        except Exception as e:
            logging.exception("Error while updating after scaling:")





