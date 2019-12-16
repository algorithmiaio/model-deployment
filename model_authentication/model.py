import Algorithmia
from tensorflow import keras
import numpy as np
import pickle
import hashlib

def sha256_checksum(filename, block_size=65536):
    # Let's read in 64KB chunks
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()

def authenticate_model(model_file, checksum):
    print("Asserting {}=={}".format(sha256_checksum(model_file), checksum))
    assert(sha256_checksum(model_file)==checksum)

# Create our Algorithmia client
client = Algorithmia.client()

# Our model file checksum
model_file_checksum = "<MODEL_FILE_CHECKSUM>"

# Define where our model file lives in our data collection
data_model = "data://<DATA_DIR>/model.h5"

# Download & initialize our model
model_file = client.file(data_model).getFile().name

# Authenticate model file before doing anything
authenticate_model(model_file, model_file_checksum)

model = keras.models.load_model(model_file)

def preprocess_input(two_d_array):
    # Check if the dimensions are 28 x 28
    assert(len(two_d_array[0])==28)
    assert(len(two_d_array[1])==28)
    np_array = np.array(two_d_array)
    # Expand dimension by 1 for model consumption
    np_array = (np.expand_dims(np_array,0))
    return np_array

def apply(input):
    # Get input text
    input_vector = preprocess_input(input)
    # Get probability using our model
    preds = model.predict(input_vector)
    probs = list(map(lambda x: float(x), preds[0]))
    # Return result back to user
    return {"prob": probs}