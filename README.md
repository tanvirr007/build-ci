# **Build-CI**  
This script automates the process of compiling Android ROMs, notifying progress on Telegram, and uploading the final file to PixelDrain.  

---

## **Supported Features**  
1. Automatically build Android ROMs.
2. Monitor build progress and system resource usage in real-time.
3. Upload the final build file to PixelDrain.
4. Send notifications to Telegram for each process (build, upload, etc.).

---

## **Requirements**  
Before using this script, ensure the following are installed on your system:
1. **Python**: Version 3.8 or newer.
2. **System Dependencies**:
   - `curl`: Used for uploading files to PixelDrain.
3. **Python Dependencies**: Listed in the `requirements.txt` file.

---

## **Installation**  
Follow these steps to install and prepare the script for usage:

1. Download the required files to the home directory of your ROM:
   ```bash
   curl -O https://raw.githubusercontent.com/knyprjkt/build-ci/main/build.py
   curl -O https://raw.githubusercontent.com/knyprjkt/build-ci/main/requirements.txt
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   '''

---

## **How to Use**
1. Once everything is set up, you can use the script as follows:
   ```bash
   python3 build.py
   ```
