import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil

class ImageUploader(FileSystemEventHandler):
    def __init__(self, watch_folder, uploaded_folder, upload_url):
        
        """
    Initializes the ImageUploader class with the specified folders and upload URL.

    Args:
        watch_folder (str): The folder to monitor for new image files.
        uploaded_folder (str): The folder to move the uploaded image files to.
        upload_url (str): The URL to upload the image files to.
    """

        self.watch_folder = watch_folder
        self.uploaded_folder = uploaded_folder
        self.upload_url = upload_url
        self.processing_files = set()

    def on_created(self, event):
        """
        Watchdog event handler for when a file is created in the watch folder.

        This function is called by watchdog when a file is created in the watch folder.
        If the file is an image file (with a .jpg, .jpeg or .png extension), it waits for 30 seconds
        and then calls the `upload_file` method to upload the file to the specified URL.
        The file path is stored in `self.processing_files` set to prevent multiple uploads of the same file.
        """
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                if str(file_path) not in self.processing_files:
                    self.processing_files.add(str(file_path))
                    # Wait for file to be completely written
                    time.sleep(30)
                    self.upload_file(str(file_path))

    def upload_file(self, file_path):
        """
        Uploads the given file using the provided upload_url.

        Moves the file to the uploaded_folder after a successful upload.

        Args:
            file_path (str): The path of the file to upload.

        Raises:
            Exception: Any error that occurs during the upload process.
        """
        try:
            if not os.path.exists(file_path):
                print(f"File no longer exists: {file_path}")
                return

            # Updated curl command with correct attribute name
            curl_command = [
                'curl',
                '-X', 'POST',
                '-F', f'imageFile=@{file_path}',
                self.upload_url
            ]

            result = subprocess.run(curl_command, capture_output=True, text=True)

            if result.returncode == 0:
                file_name = os.path.basename(file_path)
                destination = os.path.join(self.uploaded_folder, file_name)
                
                # Handle case where destination file already exists
                if os.path.exists(destination):
                    base, ext = os.path.splitext(destination)
                    counter = 1
                    while os.path.exists(f"{base}_{counter}{ext}"):
                        counter += 1
                    destination = f"{base}_{counter}{ext}"

                # Use shutil.move instead of os.rename for cross-device operations
                shutil.move(file_path, destination)
                print(f"Successfully uploaded and moved: {file_name}")
            else:
                print(f"Failed to upload: {file_path}")
                print(f"Error: {result.stderr}")

        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
        finally:
            self.processing_files.remove(file_path)

def main():
   
    """
    Monitors a folder for new images and uploads them to a specified URL.

    This function will watch the specified folder for new files, wait for 30 seconds
    before uploading the file, and then move the file to the uploaded folder.

    The folder to monitor, the folder to move the uploaded files to, and the URL
    to upload to can be configured by changing the values of the `watch_folder`,
    `uploaded_folder`, and `upload_url` variables, respectively.

    The script will continue to run until it is stopped by pressing Ctrl+C.

    :param watch_folder: The folder to watch for new images
    :type watch_folder: str
    :param uploaded_folder: The folder to move the uploaded images to
    :type uploaded_folder: str
    :param upload_url: The URL to upload the images to
    :type upload_url: str
    """

    watch_folder = "D:/cam"  
    uploaded_folder = "D:/cam/uploaded" 
    upload_url = "https://projects.benax.rw/f/o/r/e/a/c/h/p/r/o/j/e/c/t/s/4e8d42b606f70fa9d39741a93ed0356c/iot_testing_202501/upload.php"
  

    # Create uploaded folder if it doesn't exist
    Path(uploaded_folder).mkdir(parents=True, exist_ok=True)

    # Initialize event handler and observer
    event_handler = ImageUploader(watch_folder, uploaded_folder, upload_url)
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    observer.start()

    try:
        print(f"Monitoring folder: {watch_folder}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nMonitoring stopped")
    
    observer.join()

if __name__ == "__main__":
    main()