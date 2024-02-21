import os
import re
import shutil
import tempfile
from base64 import b32encode
from hashlib import sha1

from werkzeug.utils import safe_join, secure_filename


class ImageManager:
    """
    Class that manages the images of the wiki.
    It can save, optimize and delete images.
    """

    def __init__(self, app, cfg):
        self.logger = app.logger
        self.cfg = cfg
        self.images_path = os.path.join(self.cfg.wiki_directory, self.cfg.images_route)
        self.temp_dir = "/tmp/wikmd/images"
        # Execute the needed programs to check if they are available. Exit code 0 means the programs were executed successfully
        self.logger.info("Checking if webp is available for image optimization ...")
        self.can_optimize = os.system("cwebp -version") == 0 and os.system("gif2webp -version") == 0
        if not self.can_optimize and self.cfg.optimize_images in ["lossless", "lossy"]:
            self.logger.error("To use image optimization webp and gif2webp need to be installed and in the $PATH. They could not be found.")

    def save_images(self, file):
        """
        Saves the image from the filepond upload.
        The image is renamed to the hash of the content, so the image is immutable.
        This makes it possible to cache it indefinitely on the client side.
        """
        img_file = file["filepond"]
        original_file_name, img_extension = os.path.splitext(img_file.filename)

        temp_file_handle, temp_file_path = tempfile.mkstemp()
        img_file.save(temp_file_path)

        if self.cfg.optimize_images in ["lossless", "lossy"] and self.can_optimize:
            temp_file_handle, temp_file_path, img_extension = self.__optimize_image(temp_file_path, img_file.content_type)

        # Does not matter if sha1 is secure or not. If someone has the right to edit they can already delete all pages.
        hasher = sha1()
        with open(temp_file_handle, "rb") as f:
            data = f.read()
            hasher.update(data)

        # Using base32 instead of urlsafe base64, because the Windows file system is case-insensitive
        img_digest = b32encode(hasher.digest()).decode("utf-8").lower()[:-4]
        hash_file_name = secure_filename(f"{original_file_name}-{img_digest}{img_extension}")
        hash_file_path = os.path.join(self.images_path, hash_file_name)

        # We can skip writing the file if it already exists. It is the same file, because it has the same hash
        if os.path.exists(hash_file_path):
            self.logger.info(f"Image already exists '{img_file.filename}' as '{hash_file_name}'")
        else:
            self.logger.info(f"Saving image >>> '{img_file.filename}' as '{hash_file_name}' ...")
            shutil.move(temp_file_path, hash_file_path)

        return hash_file_name

    def cleanup_images(self):
        """Deletes images not used by any page"""
        saved_images = set(os.listdir(self.images_path))
        # Don't delete .gitignore
        saved_images.discard(".gitkeep")

        # Matches [*](/img/*) it does not matter if images_route is "/img" or "img"
        image_link_pattern = fr"\[(.*?)\]\(({os.path.join('/', self.cfg.images_route)}.+?)\)"
        image_link_regex = re.compile(image_link_pattern)
        used_images = set()
        # Searching for Markdown files
        for root, sub_dir, files in os.walk(self.cfg.wiki_directory):
            if os.path.join(self.cfg.wiki_directory, '.git') in root:
                # We don't want to search there
                continue
            if self.images_path in root:
                # Nothing interesting there too
                continue
            for filename in files:
                path = os.path.join(root, filename)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        matches = image_link_regex.findall(content)
                        for _caption, image_path in matches:
                            used_images.add(os.path.basename(image_path))
                except:
                    self.logger.info(f"ignoring {path}")

        not_used_images = saved_images.difference(used_images)
        for not_used_image in not_used_images:
            self.delete_image(not_used_image)

    def delete_image(self, image_name):
        image_path = safe_join(self.images_path, image_name)
        self.logger.info(f"Deleting file >>> {image_path}")
        try:
            os.remove(image_path)
        except IsADirectoryError | FileNotFoundError:
            self.logger.error(f"Could not delete '{image_path}'")

    def __optimize_image(self, temp_file_path_original, content_type):
        """
        Optimizes gif, jpg and png by converting them to webp.
        gif and png files are always converted lossless.
        jpg files are either converted lossy or near lossless depending on cfg.optimize_images.

        Uses the external binaries cwebp and gif2webp.
        """

        temp_file_handle, temp_file_path = tempfile.mkstemp()
        if content_type in ["image/gif", "image/png"]:
            self.logger.info(f"Compressing image lossless ...")
            if content_type == "image/gif":
                os.system(f"gif2webp -quiet -m 6 {temp_file_path_original} -o {temp_file_path}")
            else:
                os.system(f"cwebp -quiet -lossless -z 9 {temp_file_path_original} -o {temp_file_path}")
            os.remove(temp_file_path_original)

        elif content_type in ["image/jpeg"]:
            if self.cfg.optimize_images == "lossless":
                self.logger.info(f"Compressing image near lossless ...")
                os.system(f"cwebp -quiet -near_lossless -m 6 {temp_file_path_original} -o {temp_file_path}")
            elif self.cfg.optimize_images == "lossy":
                self.logger.info(f"Compressing image lossy ...")
                os.system(f"cwebp -quiet -m 6 {temp_file_path_original} -o {temp_file_path}")
            os.remove(temp_file_path_original)

        return temp_file_handle, temp_file_path, ".webp"
