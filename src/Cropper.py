from FaceCropper import Cropper
import threading
from Popups import ProgressBarPopup
import os
from PIL import Image



class CropperClass:
    def __init__(self,input_path,output_path,face_factor,output_size,translation):
        self.input_path = input_path
        self.output_path = output_path
        self.face_factor = face_factor
        self.output_size = output_size
        self.translation = translation


    def CropProcess(self,FaceFactor: float, OutputSize: tuple[int, int], input_path: str, output_path: str,Translation : tuple[int,int]):
        cropper = Cropper(output_size=OutputSize, face_factor=FaceFactor, strategy="largest",translation=Translation,padding="replicate")
        cropper.process_dir(input_dir=input_path, output_dir=output_path)


    def CropFaces(self,master):

        def RunCropProcess():
            try:
                self.CropProcess(self.face_factor,self.output_size, self.input_path, self.output_path, self.translation)

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








