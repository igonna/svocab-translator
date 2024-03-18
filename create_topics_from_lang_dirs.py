import languages_dataset
import sys
import os
import languages_dataset
import file_to_text

arguments = sys.argv[1:]

if len(arguments) != 2:
    print("arguments count is not 2")
    exit(1)

root_dir = os.path.expanduser(arguments[0])
output_dir = os.path.expanduser(arguments[1])

topics_names=['first_step', 'second_step', 'third_step', 'fourth_step', 'fifth_step', 'sixth_step', 'seventh_step']

query = 'insert into vocab_data.topic_words'

query = 'insert into vocab_data.topic_translations'

lang_dirs = languages_dataset.list_directories(root_dir)

def get_topic_sizes_for_lang(count):
    sizes = [200]
    while sum(sizes) < count:
        sizes.append(sizes[-1] * 2)

    if sum(sizes) > count:
        for size in sizes[:-1]:
            count -= size
        sizes[-1] = count
    
    if len(sizes) > 1:
        last = sizes.pop(-1)
        sizes[-1] += last

    return sizes

split_symbol = '\n'

def get_topics_for_sizes(words, sizes):
    topics_words = []
    first_index = 0

    for size in sizes:
        topics_words.append(words[first_index:first_index + size])
        first_index += size

    return topics_words

def get_words_from_file(file):
    text = file_to_text.read_text_file(file)
    words = text.split(split_symbol)
    words = [word[:-1] for word in words]
    return words

output_instructions = 'INSERT INTO vocab_data.topic_words (topic_tag, lang_tag, words) values'
output_instructions_translations = 'INSERT INTO vocab_data.topic_translations (topic_tag, lang_tag, lang_translation_tag, words) values'


for lang_dir in lang_dirs:
    if lang_dir[0] == '.':
        continue

    main_words = get_words_from_file(root_dir + '/' + lang_dir + '/' + 'output.txt')
    main_topics_words = get_topics_for_sizes(main_words, get_topic_sizes_for_lang(len(main_words)))
    for index, words in enumerate(main_topics_words):
        topic_text = '.'.join(words)
        file_to_text.write_text_to_file(output_dir + '/' + lang_dir + '/' + topics_names[index] + '/' + 'output.txt', topic_text)
        output_instructions += f"\n('{topics_names[index]}', '{lang_dir}', \"{topic_text}\"),"



    translation_files = languages_dataset.list_files(root_dir + '/' + lang_dir + '/translations')
    for file in translation_files:
        translation_words = get_words_from_file(file)
        translation_topic_words = get_topics_for_sizes(translation_words, get_topic_sizes_for_lang(len(translation_words)))

        translation_lang = file_to_text.get_file_name_without_extension(file)
        
        for index, words_ in enumerate(translation_topic_words):
            translation_topic_text = '.'.join(words_)
            out_path = output_dir + '/' + lang_dir + '/' + topics_names[index] + '/translations/' + file_to_text.get_file_name_without_extension(file) + '.txt'
            file_to_text.write_text_to_file(out_path, translation_topic_text)
            output_instructions_translations += f"\n('{topics_names[index]}', '{lang_dir}', '{translation_lang}', \"{topic_text}\"),"

output_instructions = output_instructions [:-1] + ';'
output_instructions_translations = output_instructions_translations [:-1] + ';'

file_to_text.write_text_to_file(output_dir + '/' + 'sql', output_instructions + '\n\n' + output_instructions_translations)