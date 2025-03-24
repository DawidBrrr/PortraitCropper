import os
import shutil
import customtkinter as ctk
import tkinter.filedialog as filedialog
import threading
from queue import Queue
from PIL import Image
from Cropper import CropperClass
from utils import save_presets, load_presets
import json
import logging


global_input_path = None
global_output_path = None


#InputData Frame
class InputsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master,fg_color="gray15")

        self.grid_columnconfigure((0, 3), weight=1)

        self.presets = load_presets()
        preset1 = next((preset for preset in self.presets.values() 
                       if preset["name"] == "Preset1"), None)
        
        # Top margin
        self.top_margin_label = ctk.CTkLabel(self, text="Górny margines")
        self.top_margin_label.grid(row=0, column=0, padx=10, pady=10, sticky="ne")
        self.tooltip_top_margin = Tooltip(self.top_margin_label, 
            "Określa wielkość górnego marginesu\nwzględem wykrytej twarzy")

        self.top_margin_slider = ctk.CTkSlider(self, from_=0, to=1, command=self.top_margin_slider_value)
        self.top_margin_slider.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        if preset1:
            self.top_margin_slider.set(preset1["top_margin"])

        self.top_margin_entry = ctk.CTkEntry(self)
        self.top_margin_entry.grid(row=0, column=2, padx=10, pady=10, sticky="nw")
        self.top_margin_entry.bind("<Return>", self.top_margin_entry_value)

        # Initialize the top entry value
        self.top_margin_entry.insert(0, str(self.top_margin_slider.get()))

        # Bottom margin 
        self.bottom_margin_label = ctk.CTkLabel(self, text="Dolny margines")
        self.bottom_margin_label.grid(row=1, column=0, padx=10, pady=10, sticky="ne")
        self.tooltip_bottom_margin = Tooltip(self.bottom_margin_label,
            "Określa wielkość dolnego marginesu\nwzględem wykrytej twarzy")

        self.bottom_margin_slider = ctk.CTkSlider(self, from_=0, to=1, command=self.bottom_margin_slider_value)
        self.bottom_margin_slider.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        if preset1:
            self.bottom_margin_slider.set(preset1["bottom_margin"])

        self.bottom_margin_entry = ctk.CTkEntry(self)
        self.bottom_margin_entry.grid(row=1, column=2, padx=10, pady=10, sticky="nw")
        self.bottom_margin_entry.bind("<Return>", self.bottom_margin_entry_value)

        # Initialize the bottom entry value
        self.bottom_margin_entry.insert(0, str(self.bottom_margin_slider.get()))

        # Left Right margin
        self.left_right_margin_label = ctk.CTkLabel(self, text="Lewo/Prawo margines")
        self.left_right_margin_label.grid(row=2, column=0, padx=10, pady=10, sticky="ne")
        self.tooltip_left_right_margin = Tooltip(self.left_right_margin_label,
            "Określa margines z lewej bądź prawej\nwzględem wykrytej twarzy")

        self.left_right_margin_slider = ctk.CTkSlider(self, from_=-1, to=1, command=self.left_right_slider_margin_value)
        self.left_right_margin_slider.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        if preset1:
            self.left_right_margin_slider.set(preset1["left_right_margin"])

        self.left_right_margin_entry = ctk.CTkEntry(self)
        self.left_right_margin_entry.grid(row=2, column=2, padx=10, pady=10, sticky="nw")
        self.left_right_margin_entry.bind("<Return>", self.left_right_entry_margin_value)

        # Initialize the left right entry value
        self.left_right_margin_entry.insert(0, str(self.left_right_margin_slider.get()))

        # Output size of an image 
        self.output_size_label = ctk.CTkLabel(self, text="Wymiary zdjęcia(x,y)")
        self.output_size_label.grid(row=3, column=0, padx=10, pady=10, sticky="ne")
        self.tooltip_size_label = Tooltip(self.output_size_label,"Kolejno x-szerokość, y-wysokosć")


        self.output_size_entryx = ctk.CTkEntry(self)
        self.output_size_entryx.grid(row=3, column=1, padx=10, pady=10, sticky="ne")
        if preset1:
            self.output_size_entryx.insert(0, str(preset1["output_size_x"]))
        else:
            self.output_size_entryx.insert(0,"1080")

        self.output_size_entryx.bind("<Return>", self.update_output_size)

        self.output_size_entryy = ctk.CTkEntry(self)
        self.output_size_entryy.grid(row=3, column=2, padx=10, pady=10, sticky="nw")
        if preset1:
            self.output_size_entryy.insert(0, str(preset1["output_size_y"]))
        else:
            self.output_size_entryy.insert(0,"1080")
        self.output_size_entryy.bind("<Return>", self.update_output_size)

        # Unit selection dropdown
        self.unit_options = ["px", "mm", "cm"]
        self.unit_var = ctk.StringVar(value=self.unit_options[0])
        self.unit_menu = ctk.CTkOptionMenu(self, variable=self.unit_var, values=self.unit_options, command=self.unit_changed)
        self.unit_menu.grid(row=3, column=3, padx=10, pady=10, sticky="nw")
    

        # DPI change section
        self.dpi_label = ctk.CTkLabel(self, text="Zmień DPI obrazu")
        self.dpi_label.grid(row=4, column=0, padx=10, pady=10, sticky="ne")
        self.tooltip_dpi_label = Tooltip(self.dpi_label,"Zmienia DPI wszystkich\n"
                                                        "zdjęć w folderze na tą wartość")

        self.dpi_entry = ctk.CTkEntry(self)
        self.dpi_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ne")
        if preset1:
            self.dpi_entry.insert(0, str(preset1["dpi"]))
        else:
            self.dpi_entry.insert(0, "96")

        #self.change_dpi_button = ctk.CTkButton(self, text="Zmień DPI", command=self.change_image_dpi)
        #self.change_dpi_button.grid(row=3, column=2, padx=10, pady=10, sticky="nw")

        #Keep track of current unit
        self.current_unit = "px"

        self.preview_frame = None

    def set_preview_frame(self, preview_frame):
        self.preview_frame = preview_frame

    def top_margin_slider_value(self, value):
        self.top_margin_entry.delete(0, ctk.END)
        self.top_margin_entry.insert(0, str(round(value, 2)))
        if self.preview_frame:
            self.preview_frame.preview_image()

    def top_margin_entry_value(self, event):
        try:
            value = float(self.top_margin_entry.get())
            if 0 <= value <= 1:
                self.top_margin_slider.set(value)
                if self.preview_frame:
                    self.preview_frame.preview_image()
                
            else:
                raise ValueError
        except ValueError:
            self.top_margin_entry.delete(0, ctk.END)
            self.top_margin_entry.insert(0, str(self.top_margin_slider.get()))

    def bottom_margin_slider_value(self, value):
        self.bottom_margin_entry.delete(0, ctk.END)
        self.bottom_margin_entry.insert(0, str(round(value, 2)))
        if self.preview_frame:
            self.preview_frame.preview_image()
        

    def bottom_margin_entry_value(self, event):
        try:
            value = float(self.bottom_margin_entry.get())
            if 0 <= value <= 1:
                self.bottom_margin_slider.set(value)
                if self.preview_frame:
                    self.preview_frame.preview_image()
            else:
                raise ValueError
        except ValueError:
            self.bottom_margin_entry.delete(0, ctk.END)
            self.bottom_margin_entry.insert(0, str(self.bottom_margin_slider.get()))


    def left_right_slider_margin_value(self, value):
        self.left_right_margin_entry.delete(0, ctk.END)
        self.left_right_margin_entry.insert(0, str(round(value, 2)))
        if self.preview_frame:
            self.preview_frame.preview_image()

    def left_right_entry_margin_value(self, event):
        try:
            value = float(self.left_right_margin_entry.get())
            if -1 <= value <= 1:
                self.left_right_margin_slider.set(value)
                if self.preview_frame:
                    self.preview_frame.preview_image()
            else:
                raise ValueError
        except ValueError:
            self.left_right_margin_entry.delete(0, ctk.END)
            self.left_right_margin_entry.insert(0, str(self.left_right_margin_slider.get()))

    def update_output_size(self, event):
        try:
            x_value = int(self.output_size_entryx.get())
            y_value = int(self.output_size_entryy.get())
            unit = self.unit_var.get()
            if self.validate_size(x_value) and self.validate_size(y_value):
                if self.preview_frame:
                    self.preview_frame.preview_image()
            else:
                raise ValueError
        except ValueError:
            self.output_size_entryx.delete(0, ctk.END)
            self.output_size_entryy.delete(0, ctk.END)
            self.output_size_entryx.insert(0, "100")
            self.output_size_entryy.insert(0, "100")

    def unit_changed(self, new_unit):
        """Convert and update the entry values based on the selected unit."""
        try:
            x_value = int(self.output_size_entryx.get())
            y_value = int(self.output_size_entryy.get())
            dpi = int(self.dpi_entry.get())

            if self.current_unit != new_unit:
                if new_unit == "px":
                    if self.current_unit == "mm":
                        x_value = int((x_value / 25.4) * dpi)
                        y_value = int((y_value / 25.4) * dpi)
                    elif self.current_unit == "cm":
                        x_value = int((x_value / 2.54) * dpi)
                        y_value = int((y_value / 2.54) * dpi)
                elif new_unit == "mm":
                    if self.current_unit == "px":
                        x_value = int((x_value / dpi) * 25.4)
                        y_value = int((y_value / dpi) * 25.4)
                    elif self.current_unit == "cm":
                        x_value = int(x_value * 10)
                        y_value = int(y_value * 10)
                elif new_unit == "cm":
                    if self.current_unit == "px":
                        x_value = int((x_value / dpi) * 2.54)
                        y_value = int((y_value / dpi) * 2.54)
                    elif self.current_unit == "mm":
                        x_value = int(x_value / 10)
                        y_value = int(y_value / 10)

                # Update the entry boxes with the new values
                self.output_size_entryx.delete(0, ctk.END)
                self.output_size_entryx.insert(0, str(x_value))
                self.output_size_entryy.delete(0, ctk.END)
                self.output_size_entryy.insert(0, str(y_value))

                self.current_unit = new_unit  # Update the current unit

        except ValueError:
            pass

    def validate_size(self, value):
        # Add validation logic here based on your requirements for size
        return 1 <= value <= 10000  # Example range

    #Legacy TODO fix it
    def get_dpi(self, folder_path):
        """Get the DPI of the first image in the specified folder."""
        try:
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    with Image.open(file_path) as img:
                        dpi = img.info.get('dpi')
                        if dpi and len(dpi) > 0:
                            print(dpi)#DEBUG
                            return dpi[0]  # Return the DPI if available
                        else:
                            print(f"No DPI information found for {file_name}, using default 96 DPI.")
                            return 96  # Return a default value if no DPI found
        except Exception as e:
            print(f"Error accessing image DPI: {e}")
        return 96  # Return a default value if no image or error


    def get_x_in_px(self, folder_path):
        """Return the x value in pixels based on the selected unit."""
        try:
            x_value = int(self.output_size_entryx.get())
            unit = self.unit_var.get()
            if unit == "px":
                return x_value
            elif unit in ["mm", "cm"]:
                dpi = int(self.dpi_entry.get())
                if unit == "mm":
                    return int((x_value / 25.4) * dpi)  # Convert mm to inches and then to pixels
                elif unit == "cm":
                    return int((x_value / 2.54) * dpi)  # Convert cm to inches and then to pixels
        except ValueError:
            return 100  # Default to 100 px if invalid

    def get_y_in_px(self, folder_path):
        """Return the y value in pixels based on the selected unit."""
        try:
            y_value = int(self.output_size_entryy.get())
            unit = self.unit_var.get()
            if unit == "px":
                return y_value
            elif unit in ["mm", "cm"]:
                dpi = int(self.dpi_entry.get())
                if unit == "mm":
                    return int((y_value / 25.4) * dpi)  # Convert mm to inches and then to pixels
                elif unit == "cm":
                    return int((y_value / 2.54) * dpi)  # Convert cm to inches and then to pixels
        except ValueError:
            return 100  # Default to 100 px if invalid


#Path Frame
class PathFrame(ctk.CTkFrame):
    def __init__(self, master,preview_frame):
        super().__init__(master,fg_color="gray15")

        self.preview_frame = preview_frame

        # Configure the grid
        self.grid_columnconfigure(1, weight=1)

        # Input folder path
        self.input_label = ctk.CTkLabel(self, text="Folder Wejściowy:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.input_entry = ctk.CTkEntry(self, width=300)
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.input_button = ctk.CTkButton(self, text="Wybierz", command=self.browse_input_folder)
        self.input_button.grid(row=0, column=2, padx=10, pady=10)

        # Output folder path
        self.output_label = ctk.CTkLabel(self, text="Folder Wyjściowy:")
        self.output_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.output_entry = ctk.CTkEntry(self, width=300)
        self.output_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.output_button = ctk.CTkButton(self, text="Wybierz", command=self.browse_output_folder)
        self.output_button.grid(row=2, column=2, padx=10, pady=10)

        #Frame for displaying images

        self.image_frame = ctk.CTkFrame(self)
        self.image_labels = []
        self.image_refs = []  # To keep a reference to CTkImage objects


    def browse_input_folder(self):
        input_path = filedialog.askdirectory()
        if input_path:
            self.input_entry.delete(0, ctk.END)
            self.input_entry.insert(0, input_path)

            self.cleanup_placeholder_folders()
            self.display_images(input_path)

            global global_input_path
            global_input_path = input_path

            # Set folder path in the PreviewFrame (this will trigger auto-preview)
            self.preview_frame.set_folder_path(input_path)
            


    def browse_output_folder(self):
        output_path = filedialog.askdirectory()
        if output_path:
            self.output_entry.delete(0, ctk.END)
            self.output_entry.insert(0, output_path)

            global global_output_path
            global_output_path = output_path

    def cleanup_placeholder_folders(self):
        #Defining Paths
        internal_data_path = "InternalData"
        edited_images_placeholder_path = os.path.join(internal_data_path,"Edited IMAGE Placeholder")
        images_placeholder_path = os.path.join(internal_data_path,"IMAGE Placeholder")

        #cleanup folders
        for folder in [edited_images_placeholder_path,images_placeholder_path]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                os.makedirs(folder)#recreating empty folders

    def display_images(self, folder_path):
        # Make the image frame visible
        self.image_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Clear previous images
        for label in self.image_labels:
            label.destroy()
        self.image_labels.clear()
        self.image_refs.clear()

        fixed_height = 100  # Fixed height for images
        # Counter to keep track of number of images displayed
        image_count = 0

        # Load and display only the first 6 images from the folder
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                if image_count >= 6:
                    break  # Stop after displaying 6 images

                image_path = os.path.join(folder_path, filename)
                image = Image.open(image_path)

                # Calculate the correct width to maintain aspect ratio
                aspect_ratio = image.width / image.height
                new_width = int(fixed_height * aspect_ratio)

                # Resize image while maintaining aspect ratio
                image = image.resize((new_width, fixed_height))

                # Convert image to CTkImage
                ctk_image = ctk.CTkImage(light_image=image, size=(new_width, fixed_height))

                # Store a reference to the image
                self.image_refs.append(ctk_image)

                # Create and pack label for each image
                label = ctk.CTkLabel(self.image_frame, image=ctk_image, text="")
                label.pack(side="left", padx=5, pady=5)
                self.image_labels.append(label)

                image_count += 1  # Increment the counter for each displayed image


#Parsing Frame
"""
class AttributeParsingFrame(ctk.CTkFrame):
    def __init__(self, master, path_frame):
        super().__init__(master)
        self.path_frame = path_frame #store reference to path frame

        self.grid_columnconfigure((0,2), weight = 1)

        self.attribute_info = ctk.CTkLabel(self, text = "Podział Cech")
        self.attribute_info.grid(row = 0 ,column = 0,padx = 10, pady = 10, sticky = "w")
        #attach tooltip
        self.tooltip = Tooltip(self.attribute_info,"Wybierz aby podzielić zdjęcia do folderów\n"
                                                   " w zależności od posiadanych przez nie cech \n")
        # Scrollable checkboxframe
        self.scrollable_checkbox_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_checkbox_frame.grid(row=0, column=1, padx=10, pady=10,rowspan=2, sticky="nsew")
        #Parse Button
        self.parse_button = ctk.CTkButton(self,text = "Podziel",command=self.image_parsing)
        self.parse_button.grid(row=1,column=0,padx=10,pady=10,sticky="w")

        # Define attributes with their corresponding numbers
        self.attributes = {
            "skóra": [1],"brwi": [2,3],
            "oczy": [4,5], "okulary": [6],
            "uszy": [7,8], "kolczyki": [9],
            "nos": [10], "zęby": [11], "wargi": [12,13],
            "szyja": [14], "naszyjnik": [15],
            "ubrania": [16], "włosy": [17], "czapka": [18]
        }
        #attribute groups to be passed into face_crop
        self.attr_groups = {}
        # Populate the scrollable frame with checkboxes
        self.checkboxes = {}
        for i, (attribute, num) in enumerate(self.attributes.items()):
            var = ctk.StringVar(value="off")
            checkbox = ctk.CTkCheckBox(self.scrollable_checkbox_frame, text=f"{attribute}",
                                       variable=var, onvalue="on", offvalue="off",
                                       command=self.on_checkbox_change)
            checkbox.grid(row=i, column=0, padx=10, pady=5,sticky="w")
            self.checkboxes[attribute] = var

    def on_checkbox_change(self):
        #clear the attr_groups
        self.attr_groups.clear()

        for attr, nums in self.attributes.items():
            if self.checkboxes[attr].get() == "on":
                self.attr_groups[attr] = nums
                self.attr_groups[f"bez_{attr}"] = [-num for num in nums]
        print(f"Selected attributes: {self.attr_groups}")
        # Add your logic here to pass the attr_groups as an argument or process further

    def image_parsing(self):
        parser = Cropper(
            det_threshold=None,
            attr_groups=self.attr_groups,
        )
        parser.process_dir(input_dir=self.path_frame.output_entry.get(),output_dir=self.path_frame.output_entry.get())


"""

#Preview Frame
class PreviewFrame(ctk.CTkFrame):
    def __init__(self, master, input_data_frame):
        super().__init__(master)
        self.input_data_frame = input_data_frame
        self.input_data_frame.set_preview_frame(self)

        self.grid_columnconfigure((0,1,2), weight=1)
        self.grid_propagate(False)

        # Preview button
        self.preview_button = ctk.CTkButton(self, text="Podgląd", command=self.preview_image)
        self.preview_button.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        # Single label for preview image
        self.preview_image_label = ctk.CTkLabel(self, text="")
        self.preview_image_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew", columnspan=3)

        # Placeholder for storing the folder path
        self.folder_path = None

        self.placeholder_folder = "InternalData/IMAGE Placeholder"
        self.edited_folder_path = "InternalData/Edited IMAGE Placeholder"  
        self.bugs_folder_path = "InternalData/Debug"

        for folder in [self.edited_folder_path, self.bugs_folder_path]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        self.processing_queue = Queue(maxsize=1)
        self.is_processing = False

        self.current_image = None
        self.current_pil_image = None
        self.fixed_height = 600
        
        # Add loading indicator
        self.loading_label = ctk.CTkLabel(self, text="Przetwarzanie...")
        self.loading_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        self.loading_label.grid_remove()  # Hide initially
        

    def set_folder_path(self, folder_path):
        """Sets the folder path where images are located and triggers initial preview."""
        self.folder_path = folder_path
        self.copy_first_image()
        self.preview_image()  # Auto-preview when folder is selected

    def copy_first_image(self):
        """Copies the first image to the placeholder folder without displaying it."""        
        if not os.path.exists(self.placeholder_folder):
            os.makedirs(self.placeholder_folder)

        if not self.folder_path:
            print("No input folder selected")
            return

        # Find and copy the first image
        for filename in os.listdir(self.folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                first_image_path = os.path.join(self.folder_path, filename)
                destination_path = os.path.join(self.placeholder_folder, os.path.basename(first_image_path))
                shutil.copy(first_image_path, destination_path)
                break

    def preview_image(self):
        # If already processing, just update the queue
        if self.is_processing:
            try:
                # Clear queue if full
                if self.processing_queue.full():
                    self.processing_queue.get_nowait()
                self.processing_queue.put_nowait(True)
            except:
                pass
            return

        # Start processing thread
        self.is_processing = True
        self.loading_label.grid()  # Show loading indicator
        threading.Thread(target=self._process_image, daemon=True).start()

    def _process_image(self):
        """Process image in background thread"""
        try:            
            CropperClass.CropProcess(self=self,
                                     input_path=self.placeholder_folder,
                                     output_path=self.edited_folder_path,
                                     debug_output=self.bugs_folder_path,
                                     res_x=int(self.input_data_frame.get_x_in_px(self.placeholder_folder)),
                                     res_y=int(self.input_data_frame.get_y_in_px(self.placeholder_folder)),
                                     top_margin_value=float(self.input_data_frame.top_margin_entry.get()),
                                     bottom_margin_value=float(self.input_data_frame.bottom_margin_entry.get()),
                                     left_right_margin_value=float(self.input_data_frame.left_right_margin_entry.get()),
                                     naming_config=None,
                                     accurate_mode=True)
            
            # Schedule UI update in main thread
            self.after(0, self._update_preview)
        except Exception as e:
            print(f"Error processing image: {e}")
            self.after(0, self._finish_processing)

    def _update_preview(self):
        """Update UI with processed image"""
        try:
            # Find first image in edited folder
            for filename in os.listdir(self.edited_folder_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    preview_image_path = os.path.join(self.edited_folder_path, filename)
                    
                    # Close previous PIL image if it exists
                    if self.current_pil_image:
                        self.current_pil_image.close()
                    
                    # Load and process image
                    image = Image.open(preview_image_path)
                    self.current_pil_image = image  # Store reference to close later
                    
                    aspect_ratio = image.width / image.height
                    new_width = int(self.fixed_height * aspect_ratio)
                    resized_image = image.resize((new_width, self.fixed_height))
                    
                    # Create new CTkImage
                    self.current_image = ctk.CTkImage(
                        light_image=resized_image, 
                        size=(new_width, self.fixed_height)
                    )
                    
                    # Update label
                    self.preview_image_label.configure(image=self.current_image)
                    
                    # Close resized image
                    resized_image.close()
                    break
        except Exception as e:
            print(f"Error updating preview: {e}")
        finally:
            self._finish_processing()

    def _finish_processing(self):
        """Clean up after processing"""
        self.loading_label.grid_remove()  # Hide loading indicator
        self.is_processing = False
        
        # Check if more updates are queued
        try:
            if not self.processing_queue.empty():
                self.processing_queue.get()
                self.preview_image()  # Process next update
        except:
            pass

    def cleanup(self):
        """Clean up image resources"""
        if self.current_pil_image:
            self.current_pil_image.close()
        self.current_pil_image = None
        self.current_image = None
        if self.preview_image_label:
            self.preview_image_label.configure(image=None)


class OutputFileNameFrame(ctk.CTkFrame):
    def __init__(self,master):
        super().__init__(master,fg_color="gray15")

        self.grid_columnconfigure(1, weight=1)

        #Change output file names
        #Structure  entryNew - DropDown(nazwaPliku, Brak) - DropDown(brak, numeracja, data, data + numeracja) - rozszerzenie(bez zmian,jpg,png,webip itd itd)
        #main Label
        self.output_file_name_label = ctk.CTkLabel(self, text="Zmiana nazwy pliku wyjściowego:")
        self.output_file_name_label.grid(row=0, column=0, padx=10, pady=10, sticky="ne")
        self.tooltip_output_file_name = Tooltip(self.output_file_name_label,
            "Zmienia nazwę plików wyjściowych\n"
            "w zależności od wybranych opcji")
        
        #NewNameEntry
        self.output_file_name_entry_label = ctk.CTkLabel(self, text="Dopisek")
        self.output_file_name_entry_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tooltip_output_file_name_entry = Tooltip(self.output_file_name_entry_label,
            "Dodaje ten tekst na początku\n"
            "nazwy każdego pliku")

        self.output_file_name_entry = ctk.CTkEntry(self)
        self.output_file_name_entry.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.output_file_name_entry.insert(0,"")

        #NameDropdown
        self.output_file_name_name_dropdown_label = ctk.CTkLabel(self, text="Nazwa")
        self.output_file_name_name_dropdown_label.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.output_file_name_name_dropdown = ctk.CTkOptionMenu(self, variable=ctk.StringVar(value="Nazwa Pliku"), values=["Nazwa Pliku","Brak"])
        self.output_file_name_name_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        #NumberingDropdown
        self.output_file_name_numbering_dropdown_label = ctk.CTkLabel(self, text="Numeracja")
        self.output_file_name_numbering_dropdown_label.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        self.output_file_name_numbering_dropdown = ctk.CTkOptionMenu(self, variable=ctk.StringVar(value="Brak"), values=["Brak","Numeracja","Data","Data + Numeracja"])
        self.output_file_name_numbering_dropdown.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")

        #ExtensionDropdown
        self.output_file_name_extension_dropdown_label = ctk.CTkLabel(self, text="Rozszerzenie")
        self.output_file_name_extension_dropdown_label.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")

        self.output_file_name_extension_dropdown = ctk.CTkOptionMenu(self, variable=ctk.StringVar(value="Bez zmian"), values=["Bez zmian","jpg", "jpeg", "png", "webp"])
        self.output_file_name_extension_dropdown.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")

    def get_naming_config(self):
        return {
            "prefix": self.output_file_name_entry.get(),
            "name": self.output_file_name_name_dropdown.get(),
            "numbering_type": self.output_file_name_numbering_dropdown.get(),                
            "extension": self.output_file_name_extension_dropdown.get()
        }
    
class TransformationsFrame(ctk.CTkFrame):
    def __init__(self,master):
        super().__init__(master,fg_color="gray15")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure((0,1,2,3), weight=1)

class ToolBarFrame(ctk.CTkFrame):
    def __init__(self,master):
        super().__init__(master,fg_color="gray15")        
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure((0,1,2,3), weight=1)

        self.input_data_frame = None

        #Load Presets
        self.presets = load_presets()
        preset_names = [preset["name"] for preset in self.presets.values()]

        #Presets segmented button
        self.preset_segment = ctk.CTkSegmentedButton(
            self,
            values=preset_names,
            command=self.on_preset_change
        )
        self.preset_segment.grid(row=0, column=1,columnspan=2, padx=10, pady=10, sticky="ew")
        self.current_preset = preset_names[0]
        self.preset_segment.set(self.current_preset)

    def save_current_preset(self):
        try:            
            #get current values
            current_values = {
                "name": self.current_preset,
                "output_size_x": int(self.input_data_frame.output_size_entryx.get()),
                "output_size_y": int(self.input_data_frame.output_size_entryy.get()),
                "dpi": int(self.input_data_frame.dpi_entry.get()),
                "top_margin": float(self.input_data_frame.top_margin_entry.get()),
                "bottom_margin": float(self.input_data_frame.bottom_margin_entry.get()),
                "left_right_margin": float(self.input_data_frame.left_right_margin_entry.get())
            }
            #Update presets dictionary
            preset_key = next(
                (key for key, preset in self.presets.items()
                 if preset["name"] == self.current_preset),None
            )
            if preset_key:
                logging.info(f"Updating preset: {self.current_preset}")
                self.presets[preset_key].update(current_values)
                save_presets(self.presets)
        except Exception as e:
            logging.info(f"Error saving preset: {e}")

    def on_preset_change(self, preset_name):
        if preset_name != self.current_preset:
            #Save current preset before switching
            self.save_current_preset()

            #Update current preset name
            self.current_preset = preset_name

            # Find the preset configuration
            preset_config = next(
                (preset for preset in self.presets.values() if preset["name"] == preset_name),
                None
            )
            
            if preset_config:

                # Update all values
                self.input_data_frame.output_size_entryx.delete(0, ctk.END)
                self.input_data_frame.output_size_entryx.insert(0, str(preset_config["output_size_x"]))
                
                self.input_data_frame.output_size_entryy.delete(0, ctk.END)
                self.input_data_frame.output_size_entryy.insert(0, str(preset_config["output_size_y"]))
                
                self.input_data_frame.dpi_entry.delete(0, ctk.END)
                self.input_data_frame.dpi_entry.insert(0, str(preset_config["dpi"]))
                
                self.input_data_frame.top_margin_slider.set(preset_config["top_margin"])
                self.input_data_frame.top_margin_entry.delete(0, ctk.END)
                self.input_data_frame.top_margin_entry.insert(0, str(preset_config["top_margin"]))

                self.input_data_frame.bottom_margin_slider.set(preset_config["bottom_margin"])
                self.input_data_frame.bottom_margin_entry.delete(0, ctk.END)
                self.input_data_frame.bottom_margin_entry.insert(0, str(preset_config["bottom_margin"]))

                self.input_data_frame.left_right_margin_slider.set(preset_config["left_right_margin"])
                self.input_data_frame.left_right_margin_entry.delete(0, ctk.END)
                self.input_data_frame.left_right_margin_entry.insert(0, str(preset_config["left_right_margin"]))
                
                # Update preview if available
                if self.input_data_frame.preview_frame:
                    self.input_data_frame.preview_frame.preview_image()
        

        





class Tooltip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.scheduled_show = None  # Track scheduled show event
        self.mouse_on_widget = False  # Track if mouse is on widget
        
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Motion>", self.on_motion)
        self.widget.bind("<Destroy>", self.on_destroy)  # Clean up on widget destruction

    def on_enter(self, event=None):
        self.mouse_on_widget = True
        # Cancel any existing scheduled show
        if self.scheduled_show:
            self.widget.after_cancel(self.scheduled_show)
        # Schedule new show
        self.scheduled_show = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event=None):
        self.mouse_on_widget = False
        # Cancel scheduled show if exists
        if self.scheduled_show:
            self.widget.after_cancel(self.scheduled_show)
            self.scheduled_show = None
        # Hide tooltip
        self.hide_tooltip()

    def on_motion(self, event):
        # Update mouse position relative to widget
        widget_bounds = (
            self.widget.winfo_rootx(),
            self.widget.winfo_rooty(),
            self.widget.winfo_rootx() + self.widget.winfo_width(),
            self.widget.winfo_rooty() + self.widget.winfo_height()
        )
        
        if not (widget_bounds[0] <= event.x_root <= widget_bounds[2] and 
                widget_bounds[1] <= event.y_root <= widget_bounds[3]):
            self.on_leave()

    def show_tooltip(self):
        if self.mouse_on_widget and not self.tooltip_window:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
            y = self.widget.winfo_rooty() + self.widget.winfo_height() // 2

            self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.attributes('-topmost', True)  # Keep tooltip on top
            tw.wm_geometry(f"+{x}+{y}")

            label = ctk.CTkLabel(tw, text=self.text, corner_radius=5)
            label.pack(padx=5, pady=5)

            # Bind events to tooltip window
            tw.bind("<Leave>", self.on_leave)
            tw.update_idletasks()  # Ensure window is created

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def on_destroy(self, event=None):
        # Clean up when widget is destroyed
        if self.scheduled_show:
            self.widget.after_cancel(self.scheduled_show)
        self.hide_tooltip()

