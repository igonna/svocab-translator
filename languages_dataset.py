import os

def list_directories(directory):
    directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return directories


def list_files(directory):
    file_paths = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and not f.startswith('.')]
    return file_paths

def get_languages_top_dirs(root_directory):
    dirs = list_directories(root_directory)
    filenames = {}
    for d in dirs:
        cur_dir_path=root_directory + '/' + d
        files = list_files(cur_dir_path)
        filenames[d] = files
    return filenames
