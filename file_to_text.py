import fitz  # Importing PyMuPDF
import os
import file



import PyPDF2
from langdetect import detect


def read_text_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def read_text_txt(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text

def get_file_name_without_extension(file_path):
    file_name_with_extension = os.path.basename(file_path)
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    return file_name_without_extension

def read_text_file(file_path):
    if file.get_file_extension(file_path) == '.pdf':
        return read_text_pdf(file_path)
    else:
        return read_text_txt(file_path)

def detect_language(text):
    return detect(text)