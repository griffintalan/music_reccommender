import flask
import pandas as pd
import numpy as np
import _pickle as pickle
from gensim.parsing.porter import PorterStemmer
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt

vocab_size_subj_obj = 5000
embedding_dimension_subj_obj = 64
max_length_subj_obj = 200
trunc_type_subj_obj = 'post'
padding_type_subj_obj = 'post'
oov_tok_subj_obj = '<OOV>'

vocab_size_sent = 5000
embedding_dimension_sent = 10
max_length_sent = 1000
trunc_type_sent = 'post'
padding_type_sent = 'post'
oov_tok_sent = '<OOV>'

# Defining function for input preprocessing
def preprocess(data, stem_data, remove_stopwords):
    processed = []
    stemmer = PorterStemmer()
    for file in data:

        # lowercasing all text

        file = str(file).lower()


        # removing non-alpha characters
        file = re.sub('[^a-zA-Z]', ' ', file)

        # tokenizing articles
        tokenized = word_tokenize(file)

        # removing stop words from tokens
        stop_removed_tokens = []
        if remove_stopwords:
            for word in tokenized:
                if word not in stop_words:
                    stop_removed_tokens.append(word)
        else:
            stop_removed_tokens = tokenized
        if stem_data:
            stemmed = []
            for token in stop_removed_tokens:
                stemmed.append(stemmer.stem(token))
            processed.append(stemmed)
        else:
            processed.append(stop_removed_tokens)
    return processed


# loading models and tokenizers
model_subj_obj = load_model('./model/subj_obj_model.h5')

with open('./model/tokenizer_subj_obj.pickle', 'rb') as handle:
    tokenizer_subj_obj = pickle.load(handle)

model_sent = load_model('./model/sent_model.h5')

with open('./model/tokenizer_sent.pickle', 'rb') as handle:
    tokenizer_sent = pickle.load(handle)


app = flask.Flask(__name__, template_folder='templates')

@app.route('/', methods = ['GET', 'POST'])
def main():
    return flask.render_template('main.html')


@app.route('/sentiment/', methods = ['GET', 'POST'])
def main_sent():
    if flask.request.method == 'GET':
        return flask.render_template('sentiment.html')
    if flask.request.method == 'POST':
        text = [flask.request.form['text']]
        processed_text = preprocess(text, stem_data = False, remove_stopwords = False)
        text_sequences_sent = tokenizer_sent.texts_to_sequences(processed_text)
        text_padded_sent = pad_sequences(text_sequences_sent,
                                     maxlen=max_length_sent,
                                     padding=padding_type_sent,
                                     truncating=trunc_type_sent)
        prediction = model_sent.predict(text_padded_sent)[0][0]
        prediction = round(prediction, 4)
        return flask.render_template('sentiment.html',
                                     original_input={'text':text[0]},
                                     result=prediction)

@app.route('/subjectivity/', methods = ['GET', 'POST'])
def main_subj():
    if flask.request.method == 'GET':
        return flask.render_template('subjectivity.html')
    if flask.request.method == 'POST':
        text = [flask.request.form['text']]
        processed_text = preprocess(text, stem_data = False, remove_stopwords = False)
        text_sequences_subj_obj = tokenizer_subj_obj.texts_to_sequences(processed_text)
        text_padded_subj_obj = pad_sequences(text_sequences_subj_obj,
                                     maxlen=max_length_subj_obj,
                                     padding=padding_type_subj_obj,
                                     truncating=trunc_type_subj_obj)
        prediction = model_sent.predict(text_padded_subj_obj)[0][0]
        prediction = round(prediction, 4)
        return flask.render_template('subjectivity.html',
                                     original_input={'text':text[0]},
                                     result=prediction)

if __name__ == '__main__':
    app.run()
