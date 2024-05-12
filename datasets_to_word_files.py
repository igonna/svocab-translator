from collections import Counter
import sys
import os
import loc_lib.file_to_text as file_to_text
import loc_lib.languages_dataset as languages_dataset
import loc_lib.text_to_words as text_to_words
import re

import loc_lib.google_translate as google_translate

arguments = sys.argv[1:]

print(arguments)

if len(arguments) != 2: # input and output dirs
    print("arguments count is not 2")
    exit(1)
    
root_dir = os.path.expanduser(arguments[0])
output_dir = os.path.expanduser(arguments[1])

langs_dir = languages_dataset.get_languages_top_dirs(root_dir)

for lang in langs_dir:
    if lang != 'en':
        continue
    files = langs_dir[lang]
    
    files_words_frequencies = []
    all_unique_words = set()
    for file in files:
        if file_to_text.get_file_name_without_extension(file)[0] == '-':
            continue
        text = file_to_text.read_text_file(file).lower()
        
        words_counts = text_to_words.text_to_words_1(text, lang)
        count_keys = len(words_counts)
        word_frequencies = {key: value / count_keys for key, value in words_counts.items()}
        files_words_frequencies.append(word_frequencies)
        all_unique_words.update(words_counts.keys())
        
        file_to_text.write_text_to_file(output_dir + '/' + lang + '/' + file_to_text.get_file_name_without_extension(file) + '.txt', ', '.join(word_frequencies.keys()))
        
        
        
    files_count = len(files_words_frequencies)
    
    result_words = {}
    
    for word in all_unique_words:
        freq_sum = 0
        word_exists_in_file_count = 0
        for words_frequencies in files_words_frequencies:
            if word in words_frequencies:
                word_exists_in_file_count += 1
                freq_sum += words_frequencies[word]

        if word_exists_in_file_count == files_count:
            result_words[word] = freq_sum





    # print(len(all_unique_words))
    
    
    sorted_words = sorted(result_words.items(), key=lambda x: x[1], reverse=True)
    
    words_keys = [word for word, _ in sorted_words]
    
    result = '\n'.join(words_keys)

    file_to_text.write_text_to_file(output_dir + '/' + lang + '.txt', result)
    # exit(0)
    
