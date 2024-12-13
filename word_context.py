import tensorflow as tf
from transformers import BertTokenizer, TFBertModel

# Load pre-trained BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = TFBertModel.from_pretrained('bert-base-uncased')

# Function to get BERT embeddings for a sentence
def get_word_embeddings(sentence):
    inputs = tokenizer(sentence, return_tensors='tf')
    outputs = model(**inputs)
    last_hidden_states = outputs.last_hidden_state
    return inputs, last_hidden_states

# Example sentence
sentence = "The quick brown fox jumps over the lazy dog."

# Get BERT embeddings
inputs, embeddings = get_word_embeddings(sentence)

# Print embeddings shape
print(f"Embeddings shape: {embeddings.shape}")

# Find the embedding of a specific word (e.g., "fox")
tokens = tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
word_index = tokens.index('fox')
word_embedding = embeddings[0][word_index]

print(f"Embedding for 'fox': {word_embedding}")
