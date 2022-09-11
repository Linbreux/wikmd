import os
import re

from config import WikmdConfig


def cleanup_images(app):
    """Deletes images not used by any page"""
    cfg = WikmdConfig()
    # Doesn't delete non image files, for example .gitignore
    saved_images = {file for file in os.listdir(app.config['UPLOAD_FOLDER']) if
                    os.path.splitext(file)[1][1:] in cfg.image_allowed_mime}

    # Matches [*](/img/*) it does not matter if images_route is "/img" or "img"
    image_link_pattern = fr"\[(.*?)\]\(({os.path.join('/', cfg.images_route)}.+?)\)"
    image_link_regex = re.compile(image_link_pattern)
    used_images = set()
    # Searching for Markdown files
    for root, sub_dir, files in os.walk(cfg.wiki_directory):
        if os.path.join(cfg.wiki_directory, '.git') in root:
            # We don't want to search there
            continue
        if os.path.join(cfg.wiki_directory, cfg.images_route) in root:
            # Nothing interesting there too
            continue
        for filename in files:
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf8", errors="ignore") as f:
                content = f.read()
                matches = image_link_regex.findall(content)
                for _caption, image_path in matches:
                    used_images.add(os.path.basename(image_path))

    not_used_images = saved_images.difference(used_images)
    for not_used_image in not_used_images:
        not_used_image_path = os.path.join(app.config['UPLOAD_FOLDER'], not_used_image)
        app.logger.info(f"Deleting file >>> {not_used_image_path}")
        try:
            os.remove(not_used_image_path)
        except IsADirectoryError | FileNotFoundError:
            app.logger.error(f"Unused image file '{not_used_image}' could not be deleted.")
