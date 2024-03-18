import json
import google_translate
import re

topic_langs = {
    'first_step':   ['en', 'es', 'it', 'de', 'ru', 'zh', 'fr', 'pt'],
    'second_step':  ['en', 'es', 'it', 'de', 'ru', 'zh', 'fr', 'pt'],
    'third_step':   ['en', 'es', 'it', 'de', 'ru', 'zh', 'fr'],
    'fourth_step':  ['en', 'es', 'it', 'de', 'ru', 'zh'],
}

names = {
    'first_step': 'first step',
    'second_step': 'second step',
    'third_step': 'third step',
    'fourth_step': 'fourth step',
}

topics_names = ['first_step', 'second_step', 'third_step', 'fourth_step']

popularity = {
    'first_step':   100,
    'second_step':  99,
    'third_step':   98,
    'fourth_step':  97,
}

premium_required = {
    'first_step':   False,
    'second_step':  False,
    'third_step':   True,
    'fourth_step':  True,
}

topic_type = {
    'first_step':   'one-to-many',
    'second_step':  'one-to-many',
    'third_step':   'one-to-many',
    'fourth_step':  'one-to-many',
}

# CREATE TABLE vocab_data.topics (
#     topic_tag VARCHAR(100) PRIMARY KEY,
#     translation_type translation_type NOT NULL,
#     title_translations JSONB NOT NULL,
#     supported_langs CHAR(2)[] NOT NULL,
#     premium_required BOOLEAN NOT NULL DEFAULT TRUE,
#     popularity SMALLINT NOT NULL
# );



src_lang = 'en'
dst_langs = ['en', 'es', 'it', 'de', 'ru', 'zh', 'fr', 'pt']

names_batched = ''
split_symbol = '.\n'
for code, name in names.items():
    names_batched += name + split_symbol


names_translated = {}
names_keys = list(names.keys())

def remove_non_character_symbols(string):
    pattern = r'[^\w\s]'
    cleaned_string = re.sub(pattern, '', string)
    return cleaned_string

for dst_lang in dst_langs:
    translated_names = google_translate.translate_text(names_batched, src_lang, dst_lang).lower()
    words = [word.strip() for word in translated_names.split('\n') if word.strip()]

    for index, word in enumerate(words):
        topic_tag = names_keys[index]
        if topic_tag not in names_translated:
            names_translated[topic_tag] = {}

        names_translated[topic_tag][dst_lang] = remove_non_character_symbols(word)
    

# names_translated = {'first_step': {'en': 'first step', 'es': 'primer paso', 'it': 'primo passo', 'de': 'erster schritt', 'ru': 'первый шаг', 'zh': '第一步', 'fr': 'premier pas', 'pt': 'primeiro passo'}, 'second_step': {'en': 'second step', 'es': 'segundo paso', 'it': 'secondo passo', 'de': 'zweiter schritt', 'ru': 'второй шаг', 'zh': '第二步', 'fr': 'deuxième étape', 'pt': 'segundo passo'}, 'third_step': {'en': 'third step', 'es': 'tercer paso', 'it': 'terzo passo', 'de': 'dritter schritt', 'ru': 'третий шаг', 'zh': '第三步', 'fr': 'troisième étape', 'pt': 'terceiro passo'}, 'fourth_step': {'en': 'fourth step', 'es': 'cuarto paso', 'it': 'quarto passo', 'de': 'vierter schritt', 'ru': 'четвертый шаг', 'zh': '第四步', 'fr': 'quatrième étape', 'pt': 'quarta etapa'}}


output_instructions = 'INSERT INTO vocab_data.topics (topic_tag, translation_type, title_translations, supported_langs, premium_required, popularity) values'


def get_dict_with_keys(orig_dict, keys):
    new_dict = {}
    for key in keys:
        if key in orig_dict:
            new_dict[key] = orig_dict[key]
    return new_dict


for topic_tag in names:
    title_translations = json.dumps(names_translated[topic_tag], ensure_ascii=False)
    output_instructions += f"\n('{topic_tag}', '{topic_type[topic_tag]}', '{title_translations}', ARRAY {str(topic_langs[topic_tag])}, {str(premium_required[topic_tag]).lower()}, {popularity[topic_tag]}),"

output_instructions = output_instructions [:-1] + ';'

print(output_instructions)