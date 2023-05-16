import os


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