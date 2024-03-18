import json
import google_translate
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

# CREATE TABLE vocab_data.topics (
#     topic_tag VARCHAR(100) PRIMARY KEY,
#     translation_type translation_type NOT NULL,
#     title_translations JSONB NOT NULL,
#     supported_langs CHAR(2)[] NOT NULL,
#     premium_required BOOLEAN NOT NULL DEFAULT TRUE,
#     popularity SMALLINT NOT NULL
# );

output_instructions = 'INSERT INTO vocab_data.topics (topic_tag, translation_type, title_translations, title_translations, supported_langs, premium_required, popularity) values'

names_batched = ''
for code, name in names.items():
    names_batched += name + '.\n'


lang_codes = list(names.keys())

for lang_code in lang_codes:
    translated_names = google_translate.translate_text(names_batched, names_src_lang, lang_code)
    words = [word.strip() for word in translated_names.split('\n') if word.strip()]

    translations_row = {}
    for index, word in enumerate(words):
        translations_row[lang_codes[index]] = remove_non_character_symbols(word.split(' ', 1)[0].lower())

    translations_row_str = json.dumps(translations_row, ensure_ascii=False)

    output_instructions += f"\n('{lang_code}', {popularities[lang_code]}, '{translations_row_str}'),"

output_instructions = output_instructions [:-1] + ';'

print(output_instructions)