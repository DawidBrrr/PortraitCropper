# PortraitCropper

PortraitCropper is a Python application for automatically cropping large numbers of portrait photos. It supports face detection, configurable margins, sensitivity adjustment, and batch processing.

After configuring the desired parameters, it will process all images in the specified folder in the same manner.

---

## Features

- **Face Detection:** Automatically detects faces in images for precise cropping.
- **Margin Configuration:** Set top, bottom, left, and right margins relative to detected faces.
- **Sensitivity Control:** Fine-tune the responsiveness of the slider and buttons using preset sensitivity levels (x1, x2, x5, x10).
- **Batch Processing:** Processing multiple images at once to speed up the process.
- **Accurate Mode:** Two-stage cropping for high-quality results.
- **Custom Naming:** Flexible output file naming options.
- **DPI Adjustment:** Change the DPI of output images.
- **Preview:** Visual preview of cropping before processing.

---

## Gui

<img width="1923" height="1028" alt="Zrzut ekranu (306)" src="https://github.com/user-attachments/assets/d074d0de-6bf4-407c-b5ba-079dfa47be48" />


---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/PortraitCropper.git
   cd PortraitCropper
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

1. **Run the application:**
   ```bash
   python src/main.py
   ```

2. **Select input and output folders.**
3. **Configure cropping parameters (margins, sensitivity, output size, DPI, etc.).**
4. **Choose cropping mode (Fast or Accurate).**
5. **Preview the cropping result.**
6. **Start batch cropping.**
7. **Check the output folder for processed images.**

---

