import loc_lib.file_to_text as file_to_text
import sys
from colorama import Back
import os
import json
import psycopg2
import re
import openai_utils
import colorama
import openai_translate_app_utils

colorama.init(autoreset=True)

arguments = sys.argv[1:]

# get arguments && verify that valid paths
if len(arguments) != 1:
    print(Back.RED + "give me path to your project root")
    exit(1)

path_to_root = arguments[0]

l10n_exists = os.path.isdir(os.path.join(path_to_root, 'l10n'))
lib_exists = os.path.isdir(os.path.join(path_to_root, 'lib'))

if not l10n_exists or not lib_exists:
    print(Back.RED + "not valid path, root not contains l10n or lib directories")
    exit(1)

language_codes_file = os.path.expanduser(path_to_root) + '/lib/main.dart'
phrases_file = os.path.expanduser(path_to_root) + '/l10n/app_en.arb'
output_dir = os.path.expanduser(path_to_root) + '/l10n'

# extract phrases && language codes && get special_phrases_variables
phrases = {}
try:
    phrases = json.loads(file_to_text.read_text_file(phrases_file))
except Exception as e:
    print(f"Phrases parse error: {e}")
    exit(1)

language_codes = []
try:
    language_codes = openai_translate_app_utils.extract_language_codes_from_file(language_codes_file)
except Exception as e:
    print(f"Exctract language codes error: {e}")
    exit(1)
    
special_phrases_variables = openai_translate_app_utils.extract_special_phrases_variables(phrases)

# translate all phrases
src_lang_code = 'en'

db_conn = psycopg2.connect(
  dbname="svocab_ai_translations",
  user="svocab_ai_translator",
  password="12345",
)

db_cur = db_conn.cursor()

src_phrases_count = len(phrases)

for dst_lang_code in language_codes:
    if dst_lang_code == src_lang_code:
        continue

    if dst_lang_code != 'ru':
        continue

    dst_lang_name = openai_translate_app_utils.get_language_name(dst_lang_code)

    translated_phrase_count = 0
    dst_phrases = {}
    for phrase_key in phrases:
        src_phrase = phrases[phrase_key]
        phrase_info = openai_translate_app_utils.get_phrase_info(phrase_key, src_phrase, special_phrases_variables)

        if not phrase_info.is_phrase_for_translation:
            dst_phrases[phrase_key] = phrases[phrase_key]
            continue

        phrase_translation_db = openai_translate_app_utils.get_phrase_from_db(db_cur, dst_lang_code, src_lang_code, src_phrase)
        if phrase_translation_db is not None:
            dst_phrases[phrase_key] = phrase_translation_db
            translated_phrase_count += 1
            continue

        # generation required
        max_retry = 3
        retry_count = 0
        translated_phrase = ''
        while(retry_count < max_retry and translated_phrase == ''):
            prompt_result = ''
            if phrase_info.phrase_type == openai_translate_app_utils.PhraseType.DEFAULT:
                prompt_result = openai_translate_app_utils.openai_default_phrase_translation(src_phrase, dst_lang_name)
            elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.VARIABLE:
                prompt_result = openai_translate_app_utils.openai_variable_phrase_translation(src_phrase, dst_lang_name)
            elif phrase_info.phrase_type == openai_translate_app_utils.PhraseType.PLURAL:
                prompt_result = openai_translate_app_utils.openai_plural_phrase_translation(src_phrase, dst_lang_name)

            translated_phrase = openai_translate_app_utils.extract_phrase_from_prompt(prompt_result)

            print(f"prompt result: {translated_phrase}")
            
            dst_phrase_info = openai_translate_app_utils.get_phrase_info(phrase_key, translated_phrase, special_phrases_variables)
            
            # correct phrase
            if phrase_info.start_non_alpha_symbol != dst_phrase_info.start_non_alpha_symbol:
                translated_phrase = phrase_info.start_non_alpha_symbol + translated_phrase

            if phrase_info.end_non_alpha_symbol != dst_phrase_info.end_non_alpha_symbol:
                translated_phrase = translated_phrase + phrase_info.start_non_alpha_symbol

            # verify that phrase valid
            try:
                if phrase_info.phrase_variables != dst_phrase_info.phrase_variables:
                    raise Exception("variables not the same")

                if phrase_info.phrase_type != dst_phrase_info.phrase_type:
                    raise Exception("phrase type not the same")

            except Exception as e:
                print(Back.YELLOW + f"Retrying: {src_phrase}; prompt: {prompt_result} reason: {e}")
                retry_count += 1
                translated_phrase = ''

        translation_valid = translated_phrase != ''
        if translation_valid:
            # add phrase to db
            openai_translate_app_utils.add_phrase_to_db(
                db_conn,
                db_cur,
                openai_translate_app_utils.PhraseData(src_lang_code, src_phrase, dst_lang_code, translated_phrase)
            )

            dst_phrases[phrase_key] = translated_phrase
            print(Back.GREEN + f"dst_lang: {dst_lang_name}; phrase: {phrases[phrase_key]}; translation: {translated_phrase}")
        else:
            print(Back.RED + f"failed to translate src_phrase: {phrases[phrase_key]}")
    
    dst_phrases_count = len(dst_phrases)
    if src_phrases_count != dst_phrases_count:
        print(Back.RED + f"Not enough translations for {dst_lang_code}, {src_phrases_count}/{dst_phrases_count}")
    else:
        filename = f"app_{dst_lang_code}.arb"
        with open(output_dir + '/' + filename, 'w') as f:
            json.dump(dst_phrases, f, ensure_ascii=False, indent=2)