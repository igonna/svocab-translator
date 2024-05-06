from collections import Counter
import sys
import os
import lib.file_to_text as file_to_text
import lib.languages_dataset as languages_dataset
import lib.text_to_words as text_to_words

import lib.google_translate as google_translate

arguments = sys.argv[1:]

if len(arguments) != 2: # input and output dirs
    print("arguments count is not 2")
    exit(1)

root_dir = os.path.expanduser(arguments[0])
output_dir = os.path.expanduser(arguments[1])

langs_dir = languages_dataset.get_languages_top_dirs(root_dir)

for lang in langs_dir:
    files = langs_dir[lang]
    for file in files:
        text = file_to_text.read_text_file(file)
        file_to_text.write_text_to_file(output_dir + '/' + lang + '/' + file_to_text.get_file_name_without_extension(file) + '.txt', text)