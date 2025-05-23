from FastCropper import image_processing
from AccurateCropper import Cropper
import threading
import shutil
import math
from Popups import CroppingProgressBarPopup
import os
from PIL import Image

class CropperClass:
    def __init__(self,input_path,output_path,debug_output,res_x,res_y,top_margin_value,bottom_margin_value,left_right_margin_value,naming_config,accurate_mode):
        self.input_path = input_path
        self.output_path = output_path
        self.debug_output = debug_output        
        self.res_x = res_x
        self.res_y = res_y     
        self.top_margin_value = top_margin_value
        self.bottom_margin_value = bottom_margin_value
        self.left_right_margin_value = left_right_margin_value
        self.naming_config = naming_config
        self.accurate_mode = accurate_mode

    
    def CropProcess(self,input_path,output_path,debug_output,res_x,res_y,top_margin_value,bottom_margin_value,left_right_margin_value,naming_config,accurate_mode):
        input_files = [os.path.join(input_path, file) for file in os.listdir(input_path)]
        temp_output = os.path.join("InternalData","temp_output")
        if not os.path.exists(temp_output):
            os.makedirs(temp_output)

        try:
            image_count = 0
            if accurate_mode:
                #Stage 1 adding 20% to margins
                temp_top = top_margin_value * 1.5
                temp_bottom = bottom_margin_value * 1.5
                temp_sides = left_right_margin_value * 1.5
                temp_res_x = int(math.ceil(res_x * 1.5))
                temp_res_y = int(math.ceil(res_y * 1.5))
                for image_path in input_files:
                    image_processing.process_image(
                        image_path=image_path,
                        error_folder=debug_output,
                        output_folder=temp_output,
                        debug_output=debug_output,
                        res_x=temp_res_x,
                        res_y=temp_res_y,
                        top_margin_value=temp_top,
                        bottom_margin_value=temp_bottom,
                        left_right_margin_value=temp_sides,
                        naming_config=naming_config,
                        image_count=image_count
                    )

                #Stage 2 Precise and final cropp
                # Compute face factor
                face_factor = 1 / (1 + top_margin_value + bottom_margin_value)
        
                # Compute translation in y-direction (vertical adjustment)
                translation_y = ((top_margin_value - bottom_margin_value) / (1 + top_margin_value + bottom_margin_value)) * res_y
        
                # Compute translation in x-direction (assumes equal left/right margin impact)
                translation_x = left_right_margin_value * res_x  



                cropper = Cropper(face_factor=face_factor,
                                  output_size=(res_x, res_y),
                                  strategy="largest",
                                  padding="replicate",
                                  translation=(translation_x, translation_y),)
                cropper.process_dir(input_dir=temp_output, output_dir=output_path)





            else:
                for image_path in input_files: # TODO in output folder create 2 folders success and error
                    image_processing.process_image(image_path=image_path,
                                            error_folder=debug_output,
                                            output_folder=output_path,
                                            debug_output=debug_output,                                        
                                            res_x=res_x,
                                            res_y=res_y,                                                                                
                                            top_margin_value = top_margin_value,
                                            bottom_margin_value = bottom_margin_value,
                                            left_right_margin_value = left_right_margin_value,
                                            naming_config = naming_config,
                                            image_count = image_count)
                image_count += 1
        except Exception as e:
            print(f"Error in Cropper: {e}")
        finally:
            if os.path.exists(temp_output):
                try:
                    shutil.rmtree(temp_output)
                except Exception as e:
                    print(f"Error cleaning up temporary directory: {e}")
        


    def CropFaces(self,master):

        def RunCropProcess():
            try:
                self.CropProcess(self.input_path,self.output_path,self.debug_output,self.res_x,self.res_y,self.top_margin_value,self.bottom_margin_value,self.left_right_margin_value,self.naming_config,self.accurate_mode)

            except Exception as e:
                print(f"Error in Cropper: {e}")
            finally:
                self.change_image_dpi()
                self.CroppingProgressBarPopup.destroy()
        try:
            self.CroppingProgressBarPopup = CroppingProgressBarPopup(master)

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








