from collections import Counter
import sys
import os
import lib.file_to_text as file_to_text
import lib.languages_dataset as languages_dataset
import lib.text_to_words as text_to_words

import lib.google_translate as google_translate

arguments = sys.argv[1:]

if len(arguments) != 2: # input and output dirs
    print("arguments count is not 2")
    exit(1)

root_dir = os.path.expanduser(arguments[0])
output_dir = os.path.expanduser(arguments[1])


langs_dir = languages_dataset.get_languages_top_dirs(root_dir)


# import re
# def clean_text(text):
#     clean_pattern = r'\b([^\w\'-])+\b'
#     cleaned_text = re.sub(clean_pattern, ' ', text)
#     return cleaned_text


langs_to_translate = ['en', 'es', 'it', 'pt', 'fr', 'de', 'ru', 'zh']

for lang in langs_dir:
    # if lang == 'zh':
        print("glob lang: " + lang)
        file_words={}
        total_word_counts = Counter()

        for file in langs_dir[lang]:
            text = file_to_text.read_text_file(file)            


            # print("lang " + file_to_text.detect_language(text) + " " + file)
            words = text_to_words.get_words_from_text(text, lang)

            word_counts = Counter(words)
            total_word_counts.update(word_counts)

            file_name = file_to_text.get_file_name_without_extension(file)

            # file_to_text.write_text_to_file(output_dir + '/' + lang + '/' + file_name + 'cleaned-text.txt', clean_text(text))


            if file_name not in file_words:
                file_words[file_name] = {}

            for word, count in word_counts.items():
                file_words[file_name][word] = ""

        sorted_word_counts = sorted(total_word_counts.items(), key=lambda item: item[1], reverse=True)

        files_count = len(file_words.keys())

        output_string = ''
        output_counted = ''
        thrown_string = ''
        to_translate = ['']
        for word, count in sorted_word_counts:
            exists_count = 0
            for file in file_words.keys():
                if word in file_words[file]:
                    exists_count += 1

            if exists_count == files_count:
                output_string += f"{word},\n"
                output_counted += f"{word},{count}\n"

                to_add = f"{word}.\n"
                if len(to_translate[-1]) + len(to_add) < 5000:
                    to_translate[-1] += to_add
                else:
                    to_translate.append(to_add)
            else:
                thrown_string += f"{word},{count}\n"


        # print(to_translate[-1])       

        for trans_lang in langs_to_translate:
            if trans_lang == lang:
                continue



            # if trans_lang != 'en':
            #     continue



            translate_result = ''
            print(f"chunks len {len(to_translate)} trans_lang: {trans_lang} glob_lang {lang}")
            for chunk in to_translate:
                good_translation=True
                # chunk_content = chunk.replace('\n', ' ')
                translated_chunk = google_translate.translate_text(chunk, lang, trans_lang)
                if translated_chunk == None:
                    good_translation=False
                    print("chunk is NONE!!!")
                print('translated')
                if len(translate_result) == 0:
                    translate_result += f"{translated_chunk}"
                else:
                    translate_result += f"\n{translated_chunk}"

            translate_result = translate_result.replace('.', ',')
            file_to_text.write_text_to_file(output_dir + '/' + lang + ('/translations/' if good_translation else '/bad-translations/' ) + trans_lang + '.txt', translate_result.lower())

            # file_to_text.write_text_to_file(output_dir + '/' + lang + '/translations/' + trans_lang + '.txt', translate_result)





        file_to_text.write_text_to_file(output_dir + '/' + lang + '/' + 'output.txt', output_string)
        # file_to_text.write_text_to_file(output_dir + '/' + lang + '/' + 'counts.txt', output_counted)
        # file_to_text.write_text_to_file(output_dir + '/' + lang + '/' + 'thrown.txt', thrown_string)



# file_to_text.get_file_name_without_extension('hello/hi/what/its.txt')
# file_to_text.read_text_file()
# english_text = "Hello, how are you? I hope you're doing well."
# clean_words = get_words_from_text(english_text, 'en')
# print(clean_words)

# korean_text = "안녕하세요, 저는 한국어 텍스트를 처리하는 방법에 대해 알아보고 있습니다."
# korean_words = get_words_from_text(korean_text, 'ko')
# print(korean_words)