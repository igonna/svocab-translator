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


def _get_words_from_international(text, lang):
    clean_pattern = r'\b([^\w\'-])+\b'
    cleaned_text = re.sub(clean_pattern, ' ', text)
    pattern = r'\b(?:[А-Яа-яA-Za-z]+(?:[\'-]?[А-Яа-яA-Za-z]+)*)\b'
    words = re.findall(pattern, cleaned_text)
    words = [word for word in words if len(word) != 1 or word in one_len_words_by_language.get(lang, [])]
    return words




one_len_words_by_language = {
    'en': {'a', 'i'},
    'es': {'y', 'o', 'u'},
    'it': {'a', 'e', 'o'},
    'pt': {'a', 'e', 'o'},
    'fr': {'à', 'c', 'ù'},
    'de': {'a', 'u', 'o'},
    'ru': {'и', 'а', 'у'}
}


words_to_remove_by_language = {
    'en': {"the", "a", "an"},
    'es': {"el", "la", "los", "las", "un", "una", "unos", "unas"},
    'it': {"il", "la", "i", "le", "un", "una", "dei", "delle"},
    'pt': {"o", "a", "os", "as", "um", "uma", "uns", "umas"},
    'fr': {"le", "la", "les", "un", "une", "des"},
    'de': {"der", "die", "das", "die", "ein", "eine", "einen", "einem", "einer", "eines", "einige", "einigen", "einiger"},
}


continue_word_chars = {'—', '-','–'}
single_quotes_chars = {'\'', "'"}
new_line_char = '\n'

def clean_word(word):
    if len(word) <= 1:
        return word
    
    start = 0
    while start < len(word) and not word[start].isalpha():
        start += 1
    
    end = len(word) - 1
    while end >= 0 and not word[end].isalpha():
        end -= 1

    return word[start:end + 1]

def text_to_words_1(text, lang):
    words_counts = {}
    add_word = lambda key: words_counts.update({key: words_counts.get(key, 0) + 1})
    
    current_word = ''
    prev_char = ''
    
    for char in text:
        if char.isalpha() or (char in single_quotes_chars and len(current_word) != 0) or char in continue_word_chars:
            current_word += char
        else:
            if len(current_word) != 0:
                if char == new_line_char and prev_char in continue_word_chars:
                    if current_word[-1] in continue_word_chars:
                        current_word[:-1]
                else:
                # if not (char == new_line_char and prev_char in continue_word_chars):
                    current_word = clean_word(current_word)
                    
                    if lang in words_to_remove_by_language:
                        if current_word in words_to_remove_by_language[lang]:
                            current_word = ''
                    
                    word_len = len(current_word)
                    if word_len != 0:
                        if word_len == 1:
                            if lang in one_len_words_by_language:
                                if current_word in one_len_words_by_language[lang]:
                                    add_word(current_word)
                                    current_word = ''
                            else:
                                add_word(current_word)
                                current_word = ''
                        else:
                            add_word(current_word)
                            current_word = ''
        prev_char = char
    return words_counts

for lang in langs_dir:
    # if lang != 'en':
    #     continue
    files = langs_dir[lang]
    
    files_words_frequencies = []
    all_unique_words = set()
    for file in files:
        if file_to_text.get_file_name_without_extension(file)[0] == '-':
            continue
        text = file_to_text.read_text_file(file).lower()
        
        words_counts = text_to_words_1(text, lang)
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
    
