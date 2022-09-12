import os
import re
import shutil
import tempfile
from base64 import b32encode
from hashlib import sha1


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

    def save_images(self, file):
        """
        Saves the image from the filepond upload.
        The image is renamed to the hash of the content, so the image is immutable.
        This makes it possible to cache it indefinitely on the client side.
        """
        img_file = file["filepond"]
        _, img_extension = os.path.splitext(img_file.filename)

        temp_file_handle, temp_file_path = tempfile.mkstemp()
        img_file.save(temp_file_path)

        # Does not matter if sha1 is secure or not, similar to git we do not overwrite files with the same hash
        hasher = sha1()
        with open(temp_file_handle, "rb") as f:
            data = f.read()
            hasher.update(data)

        # Using base32 instead of urlsafe base64, because the Windows file system is case-insensitive
        img_digest = b32encode(hasher.digest()).decode("utf-8").lower()[:-4]
        hash_file_name = f"{img_digest}{img_extension}"
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
        # Doesn't delete non image files, for example .gitignore
        saved_images = {file for file in os.listdir(self.images_path)}
        saved_images.remove(".gitignore")

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
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = image_link_regex.findall(content)
                    for _caption, image_path in matches:
                        used_images.add(os.path.basename(image_path))

        not_used_images = saved_images.difference(used_images)
        for not_used_image in not_used_images:
            self.delete_image(not_used_image)

    def delete_image(self, image_name):
        image_path = os.path.join(self.images_path, image_name)
        self.logger.info(f"Deleting file >>> {image_path}")
        try:
            os.remove(image_path)
        except IsADirectoryError | FileNotFoundError:
            self.logger.error(f"Could not delete '{image_path}'")
