from CropSense import image_processing
import threading
from Popups import ProgressBarPopup
import os
from PIL import Image


class CropperClass:
    def __init__(self,input_path,output_path,debug_output,res_x,res_y,top_margin_value,bottom_margin_value,left_right_margin_value):
        self.input_path = input_path
        self.output_path = output_path
        self.debug_output = debug_output        
        self.res_x = res_x
        self.res_y = res_y     
        self.top_margin_value = top_margin_value
        self.bottom_margin_value = bottom_margin_value
        self.left_right_margin_value = left_right_margin_value

    
    def CropProcess(self,input_path,output_path,debug_output,res_x,res_y,top_margin_value,bottom_margin_value,left_right_margin_value):
        input_files = [os.path.join(input_path, file) for file in os.listdir(input_path)]
        try:
            for image_path in input_files: # TODO in output folder create 2 folders success and error
                image_processing.process_image(image_path=image_path,
                                        error_folder=debug_output,
                                        output_folder=output_path,
                                        debug_output=debug_output,                                        
                                        res_x=res_x,
                                        res_y=res_y,                                                                                
                                        top_margin_value = top_margin_value,
                                        bottom_margin_value = bottom_margin_value,
                                        left_right_margin_value = left_right_margin_value)
        except Exception as e:
            print(f"Error in Cropper: {e}")
        


    def CropFaces(self,master):

        def RunCropProcess():
            try:
                self.CropProcess(self.input_path,self.output_path,self.debug_output,self.res_x,self.res_y,self.top_margin_value,self.bottom_margin_value,self.left_right_margin_value)

            except Exception as e:
                print(f"Error in Cropper: {e}")
            finally:
                self.change_image_dpi()
                self.ProgressBarPopup.destroy()
        try:
            self.ProgressBarPopup = ProgressBarPopup(master)

            #proces kadrowania
            threading.Thread(target=RunCropProcess).start()
        except Exception as e:
            print(f"Multithreading Error: {e}")




    def change_image_dpi(self):
        """Change the DPI of an image based on the user's input."""
        try:
            from Gui import global_dpi
            dpi_value = int(global_dpi)
            output_folder_path = self.output_path

            #Change dpi output file
            for file_name in os.listdir(output_folder_path):
                file_path = os.path.join(output_folder_path, file_name)
                if os.path.isfile(file_path):
                    with Image.open(file_path) as img:
                        img.save(file_path, dpi=(dpi_value,dpi_value))
            print(f"Image DPI changed to {dpi_value}.")
        except Exception as e:
            print(f"Error changing image DPI: {e}")








