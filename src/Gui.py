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


#Aplikacja
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        logging.info("Initializing main application window")

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

        self.output_file_name_frame = OutputFileNameFrame(self.main_container)
        self.output_file_name_frame.grid(row=5,column=2,padx=20,pady=20,sticky="nse")
        
        """
        self.attribute_parsing_frame = AttributeParsingFrame(self.main_container, self.path_frame)
        self.attribute_parsing_frame.grid(row=5, column=2, padx=20, pady=20, sticky="nse")
        """
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
                                   res_x=int(self.input_data_frame.get_x_in_px(self.path_frame.input_entry.get())),
                                   res_y=int(self.input_data_frame.get_y_in_px(self.path_frame.input_entry.get())),                                                        
                                   top_margin_value=float(self.input_data_frame.top_margin_entry.get()),
                                   bottom_margin_value=float(self.input_data_frame.bottom_margin_entry.get()),
                                   left_right_margin_value=float(self.input_data_frame.left_right_margin_entry.get()))                                                                   
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

                            # rotate image
                            rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

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
            self.preview_frame = PreviewFrame(self.main_container, self.input_data_frame)
            self.preview_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew", rowspan=5, columnspan=2)
            
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





