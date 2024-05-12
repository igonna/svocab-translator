pip3 install -r requirements.txt
python3 datasets_to_word_files.py ~/books_data ~/datasets/words_output
python3 openai_client.py ~/datasets/words_output/en.txt