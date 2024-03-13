import os

def get_file_extension(file_path):
    _, extension = os.path.splitext(file_path)
    return extension

def output_str_to_file(filepath, string):
    with open(filepath, 'w') as output_file:
        output_file.write(string)