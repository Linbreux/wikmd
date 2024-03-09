import os
import unicodedata
import re

_filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9 _.-]")
_windows_device_files = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(10)),
    *(f"LPT{i}" for i in range(10)),
}


def secure_filename(filename: str) -> str:
    """Convert your filename to be safe for the os.

    Function from werkzeug. Changed to allow space in the file name.
    """
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")
    for sep in os.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, "_")
    filename = str(_filename_ascii_strip_re.sub("", filename)).strip(
        "._"
    )
    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if (
        os.name == "nt"
        and filename
        and filename.split(".")[0].upper() in _windows_device_files
    ):
        filename = f"_{filename}"

    return filename


def pathify(path1, path2):
    """
    Joins two paths and eventually converts them from Win (\\) to linux  OS separator.
    :param path1: first path
    :param path2: second path
    :return safe joined path
    """
    return os.path.join(path1, path2).replace("\\", "/")


def move_all_files(src_dir: str, dest_dir: str):
    """
    Function that moves all the files from a source directory to a destination one.
    If a file with the same name is already present in the destination, the source file will be renamed with a
    '-copy-XX' suffix.
    :param src_dir: source directory
    :param dest_dir: destination directory
    """
    if not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)  # make the dir if it doesn't exist

    src_files = os.listdir(src_dir)
    dest_files = os.listdir(dest_dir)

    for file in src_files:
        new_file = file
        copies_count = 1
        while new_file in dest_files:  # if the file is already present, append '-copy-XX' to the file name
            file_split = file.split('.')
            new_file = f"{file_split[0]}-copy-{copies_count}"
            if len(file_split) > 1:  # if the file has an extension (it's not a directory nor a file without extension)
                new_file += f".{file_split[1]}"  # add the extension
            copies_count += 1

        os.rename(f"{src_dir}/{file}", f"{dest_dir}/{new_file}")