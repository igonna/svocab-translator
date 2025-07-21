from wordfreq import available_languages, word_frequency, top_n_list

languages = available_languages()

word_counts = {}
for lang in languages:
    count = len(set(word_frequency(word, lang) for word in top_n_list(lang, 100000000)))
    word_counts[lang] = count
    print(f"{lang}: {count} words")

