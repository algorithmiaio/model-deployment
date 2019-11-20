import Algorithmia
from tensorflow import keras
import numpy as np
import pickle

# Create our Algorithmia client
client = Algorithmia.client()

# Define where our files live in our data collection
data_model = "data://.my/mycollection/text_classification_model.h5"
data_word_index = "data://.my/mycollection/word_index.pickle"

# Download & initialize our model
model_file = client.file(data_model).getFile().name
model = keras.models.load_model(model_file)

# Download & initialize our word index
word_index_file = client.file(data_word_index).getFile().name
with open(word_index_file, "rb") as fh:
    word_index = pickle.load(fh)

# Function for vectorizing our input text
def vectorize_text(text):
    vector = []
    words = text.split(" ")
    for word in words:
        if word in word_index:
            vector.append(word_index[word])

    return keras.preprocessing.sequence.pad_sequences([np.array(vector, dtype=np.int32)],
                                               value=word_index["<PAD>"],
                                               padding='post',
                                               maxlen=256)

def apply(input):
    # Get input text
    input_text = input["text"]
    # Vectorize input text
    input_vector = vectorize_text(input_text)
    # Get probability using our model
    prob = float(model.predict(input_vector)[0][0])
    # Return result back to user
    return {"prob": prob}