from googletrans import Translator
import time
from deep_translator.exceptions import RequestError

translator = Translator()


def translate_text(text, source_lang, target_language):
    if target_language == 'zh':
        target_language = 'zh-CN'

    if source_lang == 'zh':
        source_lang = 'zh-CN'

    max_retries=6
    attempt = 0
    while attempt < max_retries:
        try:
            translation = translator.translate(text, dest=target_language, src=source_lang)
            if translation.text:
                return translation.text
            else:
                print("Translation returned None. Retrying...")
                time.sleep(3)
                attempt += 1
        except RequestError as e:
            print("Request error occurred:", str(e))
            attempt += 1
        except Exception as e:
            print("Error:", str(e))
            attempt += 1
    
    print("Maximum retries reached. Translation failed.")
    return None