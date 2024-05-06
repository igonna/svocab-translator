import lib.languages_dataset as languages_dataset
import sys
import os
import lib.languages_dataset as languages_dataset
import lib.file_to_text as file_to_text

arguments = sys.argv[1:]

if len(arguments) != 1:
    print("arguments count is not 1")
    exit(1)

root_dir = os.path.expanduser(arguments[0])

def get_ids_to_remove(words):
    ids_to_remove = set()
    for index_to_remove, word in enumerate(words):
        if word == ',':
            ids_to_remove.add(index_to_remove)
    return ids_to_remove

split_symbol = '\n'
def get_ids_to_remove_for_lang(lang_dir):
    ids_to_remove = set()
    main_text = file_to_text.read_text_file(lang_dir + '/' + 'output.txt')
    ids_to_remove = ids_to_remove.union(get_ids_to_remove(main_text.split(split_symbol)))
    
    translation_files = languages_dataset.list_files(lang_dir + '/translations')
    for file in translation_files:
        translation_text = file_to_text.read_text_file(file)
        ids_to_remove = ids_to_remove.union(get_ids_to_remove(translation_text.split(split_symbol)))
    return ids_to_remove

def remove_ids_for_lang(lang_dir, ids_to_remove):
    main_text = file_to_text.read_text_file(lang_dir + '/' + 'output.txt')
    main_result = split_symbol.join(remove_ids_from_array(main_text.split(split_symbol), ids_to_remove))
    file_to_text.write_text_to_file(lang_dir + '/' + 'output.txt', main_result)

    translation_files = languages_dataset.list_files(lang_dir + '/translations')
    for file in translation_files:
        translation_text = file_to_text.read_text_file(file)
        translation_result = split_symbol.join(remove_ids_from_array(translation_text.split(split_symbol), ids_to_remove))
        file_to_text.write_text_to_file(file, translation_result)

def remove_ids_from_array(arr, ids):
    result_arr = []
    for index, elem in enumerate(arr):
        if index in ids:
            continue
        result_arr.append(elem)
    return result_arr


lang_dirs = languages_dataset.list_directories(root_dir)

for lang_dir in lang_dirs:
    if lang_dir[0] == '.':
        continue

    print('\nglob_lang: ', lang_dir)

    current_lang_dir = root_dir + '/' + lang_dir
    print('TO REMOVE: ', get_ids_to_remove_for_lang(current_lang_dir))
    remove_ids_for_lang(current_lang_dir, get_ids_to_remove_for_lang(current_lang_dir))