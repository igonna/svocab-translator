import tiktoken

# Initialize the GPT-4 tokenizer
# You can specify "gpt-4" if you want to use the GPT-4 encoding
tokenizer = tiktoken.get_encoding("gpt-4")

# Sample Chinese text
chinese_text = "你好，世界！这是一个关于自然语言处理的示例。"

# Tokenize the text
tokens = tokenizer.encode(chinese_text)

# Display tokens (token IDs)
print("Tokens:", tokens)

# Decode tokens back to text to see how they represent the original text
decoded_text = tokenizer.decode(tokens)
print("Decoded Text:", decoded_text)

# If you want to see the words as a list
words = [tokenizer.decode([token]) for token in tokens]
print("Words:", words)