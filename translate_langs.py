import json
import loc_lib.google_translate as google_translate
import re


def remove_non_character_symbols(string):
    pattern = r'[^\w\s]'
    cleaned_string = re.sub(pattern, '', string)
    return cleaned_string

names_src_lang = 'en'
names = {
    'en':'english',
    'es':'spanish',
    'it':'italian',
    'pt':'portuguese',
    'fr':'french',
    'de':'german',
    'ru':'russian',
    'zh':'chinese'
}

popularities = {
    'en':25,
    'es':15,
    'zh':10,
    'fr':10,
    'de':8,
    'ru':4,
    'it':3,
    'pt':3,
}





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

        names_translated[topic_tag][dst_lang] = remove_non_character_symbols(word.split(' ', 1)[0].lower())



lang_codes = list(names.keys())


# output_instructions = ''

output_instructions = 'INSERT INTO vocab_data.languages (lang_tag, popularity, title_translations) values'

for lang_code in lang_codes:
    translations_row_str = json.dumps(names_translated[lang_code], ensure_ascii=False)
    output_instructions += f"\n('{lang_code}', {popularities[lang_code]}, '{translations_row_str}'),"


    # output_instructions += f"\nUPDATE vocab_data.languages SET title_translations = '{translations_row_str}' WHERE lang_tag = '{lang_code}';"

output_instructions = output_instructions [:-1] + ';'
print(output_instructions)
    
# names_batched = ''
# for code, name in names.items():
#     names_batched += name + '.\n'


# lang_codes = list(names.keys())

# for lang_code in lang_codes:
#     translated_names = google_translate.translate_text(names_batched, names_src_lang, lang_code)
#     words = [word.strip() for word in translated_names.split('\n') if word.strip()]

#     translations_row = {}
#     for index, word in enumerate(words):
#         translations_row[lang_codes[index]] = remove_non_character_symbols(word.split(' ', 1)[0].lower())

#     translations_row_str = json.dumps(translations_row, ensure_ascii=False)

#     output_instructions += f"\n('{lang_code}', {popularities[lang_code]}, '{translations_row_str}'),"

# output_instructions = output_instructions [:-1] + ';'

# print(output_instructions)