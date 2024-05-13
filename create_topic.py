import re
import loc_lib.file_to_text as file_to_text
import sys
import os
import loc_lib.text_to_words as text_to_words

arguments = sys.argv[1:]

if len(arguments) != 1:
    print("arguments count is not 1")
    exit(1)

input_file = os.path.expanduser(arguments[0])



file_to_text.read_text_file(input_file).lower().split('\n')