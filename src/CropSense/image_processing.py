import cv2
import os
import imghdr
import win32com.client
from tqdm import tqdm
import numpy as np
from CropSense import variable

def images_error(image_path, error_folder):
    shell = win32com.client.Dispatch("WScript.Shell")
    filename_shortcut = os.path.basename(image_path)
    shortcut_path = os.path.join(error_folder, filename_shortcut + ".lnk")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = os.path.abspath(image_path)
    shortcut.Save()



def process_image(image_path,
                  error_folder,
                  output_folder,
                  debug_output,                                   
                  res_x,
                  res_y,                    
                  top_margin_value, 
                  bottom_margin_value,
                  left_right_margin_value=0.0):
    error_count = 0
    endX = 0
    endY = 0
    startX = 0
    startY = 0
    i = 0
    confidence = 0
    image = ""
    output_image_path = ""
    filename = ""
    error_msg = ""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prototxt_path = os.path.join(script_dir, "deploy.prototxt.txt")
    model_path = os.path.join(script_dir, "res10_300x300_ssd_iter_140000.caffemodel")
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    
    is_error = False
    filename, extension = os.path.splitext(os.path.basename(image_path))
    image = cv2.imread(image_path)
    image_format = imghdr.what(image_path)
    supported_formats = ["jpg", "jpeg", "png", "webp"]
    if image_format is None or image_format not in supported_formats:
        print(f"\rInvalid image format or unsupported format, skipping {filename}{extension}")
        error_count += 1
    else:
        if image.shape[0] > 300 or image.shape[1] > 300:
            blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            net.setInput(blob)
            detections = net.forward()

            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                box = detections[0, 0, i, 3:7] * np.array([image.shape[1], image.shape[0], image.shape[1], image.shape[0]])
                (startX, startY, endX, endY) = box.astype(int)

                width = endX - startX
                height = endY - startY
                if confidence < variable.confidence_level:
                    print(f"\rConfidence level too low ({int(confidence * 100)}%), skipping face_{i} on {filename}{extension}")
                    error_msg = "CONFIDENCE LEVEL TOO LOW"
                    images_error(image_path, error_folder)
                    is_error = True
                    error_count += 1
                    draw_rectangle(endX,
                                    startX,
                                    endY,
                                    startY,
                                    top_margin_value,
                                    bottom_margin_value,
                                    left_right_margin_value,
                                    res_x,
                                    res_y,
                                    image,                                     
                                    output_folder,
                                    output_image_path,
                                    filename,
                                    extension,
                                    image_path,
                                    debug_output,                                    
                                    is_error,
                                    i,
                                    confidence,
                                    error_msg)
                    break
                
                if confidence > variable.confidence_level:                  
                    
                    if width < variable.min_face_res_x or height < variable.min_face_res_y:
                        print(f"\rFace resolution is too small for face crop, skipping face_{i} on {filename}{extension}")
                        error_msg = "FACE RESOLUTION IS TOO SMALL"
                        images_error(image_path, error_folder)
                        is_error = True
                        error_count += 1
                        draw_rectangle(endX,
                                        startX,
                                        endY,
                                        startY,
                                        top_margin_value,
                                        bottom_margin_value,
                                        left_right_margin_value,
                                        res_x,
                                        res_y,
                                        image,                                             
                                        output_folder,
                                        output_image_path,
                                        filename,
                                        extension,
                                        image_path,
                                        debug_output,                                        
                                        is_error,
                                        i,
                                        confidence,
                                        error_msg)
                        break
                    
                break
            for i in range(detections.shape[2]):
                if is_error == True:
                    break
                confidence = detections[0, 0, i, 2]

                # Filter out weak detections
                if confidence > variable.confidence_level:
                    box = detections[0, 0, i, 3:7] * np.array([image.shape[1], image.shape[0], image.shape[1], image.shape[0]])
                    (startX, startY, endX, endY) = box.astype(int)
                
                    width = endX - startX
                    height = endY - startY
                    is_error = draw_rectangle(endX,
                                        startX,
                                        endY,
                                        startY,
                                        top_margin_value,
                                        bottom_margin_value,
                                        left_right_margin_value,
                                        res_x,
                                        res_y,
                                        image,                                 
                                        output_folder,
                                        output_image_path,
                                        filename,
                                        extension,
                                        image_path,
                                        debug_output,                                        
                                        is_error,
                                        i,
                                        confidence,
                                        error_msg)
                else:
                    break
        else:
            print(f"\rThe resolution is too low for face detection, skipping {filename}{extension}")
            images_error(image_path, error_folder)
            error_count += 1
    return error_count

def draw_rectangle(endX,
                   startX,
                   endY,
                   startY,
                   top_margin_value,
                   bottom_margin_value,
                   left_right_margin_value,
                   res_x,
                   res_y,
                   image, 
                   output_folder,
                   output_image_path,
                   filename,
                   extension,
                   image_path,
                   debug_output,                   
                   is_error,
                   i,
                   confidence,
                   error_msg):
    # Calculate the size of the region to be cropped
    width = endX - startX
    height = endY - startY

    # Calculate aspect ratio based on target resolution
    target_aspect_ratio = res_x / res_y

    # Calculate the coordinates for the rectangular region
    rect_center_x = (endX + startX) // 2
    rect_center_y = (endY + startY) // 2

    # Calculate initial crop dimensions maintaining target aspect ratio
    if width / height > target_aspect_ratio:
        rect_height = height
        rect_width = int(height * target_aspect_ratio)
    else:
        rect_width = width
        rect_height = int(width / target_aspect_ratio)

    rect_upper_left_x = rect_center_x - rect_width // 2
    rect_upper_left_y = rect_center_y - rect_height // 2
    rect_lower_right_x = rect_upper_left_x + rect_width
    rect_lower_right_y = rect_upper_left_y + rect_height

    # Calculate margins based on the target aspect ratio
    top_margin = int(rect_height * top_margin_value)
    bottom_margin = int(rect_height * bottom_margin_value)
    
    # Calculate side margins to maintain aspect ratio
    total_height = rect_height + top_margin + bottom_margin
    target_width = int(total_height * target_aspect_ratio)
    side_margin = (target_width - rect_width) // 2
    
    # Apply margins while maintaining aspect ratio
    margin_upper_left_x = max(rect_center_x - (target_width // 2), 0)
    margin_upper_left_y = max(rect_upper_left_y - top_margin, 0)
    margin_lower_right_x = min(margin_upper_left_x + target_width, image.shape[1])
    margin_lower_right_y = min(rect_lower_right_y + bottom_margin, image.shape[0])
    
    # Adjust if we hit image boundaries
    if margin_upper_left_x == 0 or margin_lower_right_x == image.shape[1]:
        # Recalculate height to maintain aspect ratio
        available_width = margin_lower_right_x - margin_upper_left_x
        target_height = int(available_width / target_aspect_ratio)
        margin_upper_left_y = max(rect_center_y - (target_height // 2), 0)
        margin_lower_right_y = min(margin_upper_left_y + target_height, image.shape[0])

    # Calculate the center of the second box
    second_box_center_x = (margin_upper_left_x + margin_lower_right_x) // 2

    # Calculate horizontal shift to center on face
    shift_amount = second_box_center_x - ((margin_upper_left_x + margin_lower_right_x) // 2)
    margin_upper_left_x = max(margin_upper_left_x + shift_amount, 0)
    margin_lower_right_x = min(margin_lower_right_x + shift_amount, image.shape[1])

    # Modify the horizontal shift calculation to include left_right_margin_value
    horizontal_shift = int(rect_width * left_right_margin_value * -1)
    margin_upper_left_x = max(margin_upper_left_x + horizontal_shift, 0)
    margin_lower_right_x = min(margin_lower_right_x + horizontal_shift, image.shape[1])

    # If the shift would push the box outside the image bounds, adjust it
    if margin_upper_left_x == 0:
        margin_lower_right_x = min(target_width, image.shape[1])
    elif margin_lower_right_x == image.shape[1]:
        margin_upper_left_x = max(image.shape[1] - target_width, 0)

    # Crop the image to the rectangular region with margin
    rect_region = image[margin_upper_left_y:margin_lower_right_y, 
                       margin_upper_left_x:margin_lower_right_x]

    # Save the cropped and resized image TODO modifiable output paths
    output_image_path = os.path.join(output_folder, f"{filename}{extension}")
    if rect_region.size == 0:
        is_error = True
    else:
        if not is_error:
            resized_image = cv2.resize(rect_region, (res_x, res_y))
            cv2.imwrite(output_image_path, resized_image)
    
    # Calculate the thickness of the rectangle based on the image resolution
    resolution_thickness_ratio = image.shape[1] // 128
    thickness = max(resolution_thickness_ratio, 5)

    debug_image = image.copy()

    cv2.rectangle(debug_image, (startX, startY), (endX, endY), (0, 0, 255), thickness) #face rectangle
    cv2.rectangle(debug_image, (rect_upper_left_x, rect_upper_left_y), (rect_lower_right_x, rect_lower_right_y), (0, 255, 0), thickness) #crop rectagle
    cv2.rectangle(debug_image, (margin_upper_left_x, margin_upper_left_y),
              (margin_upper_left_x + rect_width, margin_upper_left_y + rect_height),
              (255,165,0), thickness)    
    font_scale = min(image.shape[1], image.shape[0]) / 1000
    font_thickness = max(1, int(min(image.shape[1], image.shape[0]) / 500))

    # FIRST TEXT LABEL
    resolution_text = f"{image.shape[1]}x{image.shape[0]} face_{i}_{width}px ({int(confidence * 100)}%)"
    background_color = (255, 255, 0)
    text_color = (0, 0, 0)
    text_size, _ = cv2.getTextSize(resolution_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)

    background_width = text_size[0] + 10
    background_height = text_size[1] + 10
    background = np.zeros((background_height, background_width, 3), dtype=np.uint8)
    background[:, :] = background_color

    # Resize the background if its width is greater than the available width in debug_image
    if background_width > debug_image.shape[1]:
        ratio = debug_image.shape[1] / background_width
        background_width = debug_image.shape[1]
        background_height = int(background_height * ratio)
        background = cv2.resize(background, (background_width, background_height))

    cv2.putText(background, resolution_text, (10, text_size[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness)
    debug_image[0:background_height, 0:background_width] = background

    # SECOND TEXT LABEL
    if is_error == True:
        second_background_color = (0, 0, 255) 
        second_text_color = (0, 0, 0)
        second_text = f"ERROR {error_msg}"
    else:
        second_background_color = (0, 255, 0) 
        second_text_color = (0, 0, 0) 
        second_text = "OK PASSED"

    second_font_scale = font_scale
    second_font_thickness = font_thickness
    second_text_size, _ = cv2.getTextSize(second_text, cv2.FONT_HERSHEY_SIMPLEX, second_font_scale, second_font_thickness)

    second_background_width = second_text_size[0] + 10
    second_background_height = second_text_size[1] + 10

    second_background = np.zeros((second_background_height, second_background_width, 3), dtype=np.uint8)
    second_background[:, :] = second_background_color

    if second_background_width > debug_image.shape[1]:
        second_ratio = debug_image.shape[1] / second_background_width
        second_background_width = debug_image.shape[1]
        second_background_height = int(second_background_height * second_ratio)
        second_background = cv2.resize(second_background, (second_background_width, second_background_height))

    cv2.putText(second_background, second_text, (10, second_text_size[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, second_font_scale, second_text_color, second_font_thickness)

    debug_image_height, debug_image_width, _ = debug_image.shape
    combined_height = background_height + second_background_height
    if combined_height > debug_image_height:
        debug_image = cv2.resize(debug_image, (debug_image_width, combined_height))
    debug_image[background_height:combined_height, 0:second_background_width] = second_background

    filename = os.path.splitext(os.path.basename(image_path))[0]
    debug_image_path = os.path.join(debug_output, f"{filename}_debug_{i}{extension}")
    cv2.imwrite(debug_image_path, debug_image)

    return is_error