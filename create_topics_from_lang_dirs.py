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

words_in_first_topic=400
topics_per_size=2

# CREATE TABLE vocab_data.topic_words (
#     topic_tag VARCHAR(100) NOT NULL REFERENCES vocab_data.topics(topic_tag),
#     lang_tag CHAR(2) NOT NULL REFERENCES vocab_data.languages(lang_tag),
#     last_update_time TIMESTAMP NOT NULL DEFAULT NOW(),
#     words TEXT NOT NULL,
#     UNIQUE(topic_tag, lang_tag)
# );


# CREATE TABLE vocab_data.topic_translations (
#     topic_tag VARCHAR(30) NOT NULL REFERENCES vocab_data.topics(topic_tag),
#     lang_tag CHAR(2) NOT NULL REFERENCES vocab_data.languages(lang_tag),
#     lang_translation_tag CHAR(2) NOT NULL REFERENCES vocab_data.languages(lang_tag),
#     last_update_time TIMESTAMP NOT NULL DEFAULT NOW(),
#     words TEXT NOT NULL,
#     UNIQUE(topic_tag, lang_tag, lang_translation_tag)
# );

query = 'insert into vocab_data.topic_words'

query = 'insert into vocab_data.topic_translations'

lang_dirs = languages_dataset.list_directories(root_dir)

for lang_dir in lang_dirs:
    if lang_dir[0] == '.':
        continue

    print('\nglob_lang: ', lang_dir)

    current_lang_dir = root_dir + '/' + lang_dir
    print('TO REMOVE: ', get_ids_to_remove_for_lang(current_lang_dir))
    remove_ids_for_lang(current_lang_dir, get_ids_to_remove_for_lang(current_lang_dir))