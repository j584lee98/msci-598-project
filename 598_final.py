# -*- coding: utf-8 -*-
"""BERT.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pD3NuICuiT90HR2iX9yddnxut55Ky_wB

# Imports
"""

from google.colab import drive
drive.mount('/content/drive/')

# Commented out IPython magic to ensure Python compatibility.
# %cd drive/MyDrive/598project/

!pip install simpletransformers

from simpletransformers.classification import ClassificationModel, ClassificationArgs

"""# Load Data"""

import os
import csv
import pandas as pd
from tqdm import tqdm

from sklearn.model_selection import train_test_split

def fnc(path_headlines, path_bodies):

    map = {
        'agree': 0,
        'disagree': 1,
        'discuss': 2,
        'unrelated': 3
    }

    with open(path_bodies, encoding='utf_8') as fb:  # Body ID,articleBody
        body_dict = {}
        lines_b = csv.reader(fb)
        for i, line in enumerate(tqdm(list(lines_b), ncols=80, leave=False)):
            if i > 0:
                body_id = int(line[0].strip())
                body_dict[body_id] = line[1]

    with open(path_headlines, encoding='utf_8') as fh: # Headline,Body ID,Stance
        lines_h = csv.reader(fh)
        h = []
        b = []
        l = []
        for i, line in enumerate(tqdm(list(lines_h), ncols=80, leave=False)):
            if i > 0:
                try:
                    body_id = int(line[1].strip())
                    label = line[2].strip()
                except:
                    continue
                if label in map and body_id in body_dict:
                    h.append(line[0])
                    l.append(map[line[2]])
                    b.append(body_dict[body_id])
    return h, b, l

data_dir = '/content/drive/MyDrive/598project/fnc-1'
headlines, bodies, labels = fnc(
    os.path.join(data_dir, 'train_stances.csv'),
    os.path.join(data_dir, 'train_bodies.csv')
)

list_of_tuples = list(zip(headlines, bodies, labels))
df = pd.DataFrame(list_of_tuples, columns=['text_a', 'text_b', 'labels'])
train_df, val_df = train_test_split(df)
labels_val = pd.Series(val_df['labels']).to_numpy()

headlines, bodies, labels = fnc(
    os.path.join(data_dir, 'competition_test_stances.csv'),
    os.path.join(data_dir, 'competition_test_bodies.csv')
)

list_of_tuples = list(zip(headlines, bodies, labels))
test_df = pd.DataFrame(list_of_tuples, columns=['text_a', 'text_b', 'labels'])
labels_test = pd.Series(test_df['labels']).to_numpy()

"""# Train Model"""

model = ClassificationModel('roberta', 'roberta-base', num_labels=4, args={
    'learning_rate':1e-5,
    'num_train_epochs': 3,
    'reprocess_input_data': True,
    'overwrite_output_dir': True,
    'process_count': 10,
    'train_batch_size': 16,
    'eval_batch_size': 16,
    'max_seq_length': 512,
    'fp16': True
})

model.train_model(train_df)

"""# Test Model

## Predictions
"""

import numpy as np
_, model_outputs_test, _ = model.eval_model(test_df)

preds_test = np.argmax(model_outputs_test, axis=1)

"""## F1 Scores"""

from sklearn.metrics import f1_score

def calculate_f1_scores(y_true, y_predicted):
    f1_macro = f1_score(y_true, y_predicted, average='macro')
    f1_classwise = f1_score(y_true, y_predicted, average=None, labels=[0, 1, 2, 3])

    resultstring = "F1 macro: {:.3f}".format(f1_macro * 100) + "% \n"
    resultstring += "F1 agree: {:.3f}".format(f1_classwise[0] * 100) + "% \n"
    resultstring += "F1 disagree: {:.3f}".format(f1_classwise[1] * 100) + "% \n"
    resultstring += "F1 discuss: {:.3f}".format(f1_classwise[2] * 100) + "% \n"
    resultstring += "F1 unrelated: {:.3f}".format(f1_classwise[3] * 100) + "% \n"

    return resultstring

print(calculate_f1_scores(preds_test, labels_test))

"""## FNC-1"""

RELATED = [0, 1, 2]

def fnc_score_cm(predicted_labels, target):
  score = 0.0
  cm = [[0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]]
  for i, (g, t) in enumerate(zip(predicted_labels, target)):
    if g == t:
      score += 0.25
      if g != 3:
        score += 0.50
    if g in RELATED and t in RELATED:
      score += 0.25

    cm[g][t] += 1
  return score, cm

"""## Confusion Matrix"""

LABELS = [0, 1, 2, 3]

def print_confusion_matrix(cm):
  lines = ['CONFUSION MATRIX:']
  header = "|{:^11}|{:^11}|{:^11}|{:^11}|{:^11}|".format('', *LABELS)
  line_len = len(header)
  lines.append("-"*line_len)
  lines.append(header)
  lines.append("-"*line_len)
  hit = 0
  total = 0
  for i, row in enumerate(cm):
    hit += row[i]
    total += sum(row)
    lines.append("|{:^11}|{:^11}|{:^11}|{:^11}|{:^11}|".format(LABELS[i], *row))
    lines.append("-"*line_len)
  lines.append("ACCURACY: {:.3f}".format((hit / total)*100) + "%")
  print('\n'.join(lines))

fnc_score, cm_test = fnc_score_cm(preds_test, labels_test)
print("\nRelative FNC Score: {:.3f}".format(100/13204.75*fnc_score) + "% \n")
print_confusion_matrix(cm_test)

"""## Generate Competition Submission Result"""

def fnc_comp_test(path_headlines, path_bodies):

    map = {
        'agree': 0,
        'disagree': 1,
        'discuss': 2,
        'unrelated': 3
    }

    with open(path_bodies, encoding='utf_8') as fb:  # Body ID,articleBody
        body_dict = {}
        lines_b = csv.reader(fb)
        for i, line in enumerate(tqdm(list(lines_b), ncols=80, leave=False)):
            if i > 0:
                body_id = int(line[0].strip())
                body_dict[body_id] = line[1]

    with open(path_headlines, encoding='utf_8') as fh: # Headline,Body ID,Stance
        lines_h = csv.reader(fh)
        h = []
        b = []
        l = []
        for i, line in enumerate(tqdm(list(lines_h), ncols=80, leave=False)):
            if i > 0:
                try:
                    body_id = int(line[1].strip())
                except:
                    continue
                if body_id in body_dict:
                    l.append([line[0], body_dict[body_id]])
                    h.append(line[0])
                    b.append(body_id)
    return h, b, l

answer_headlines, answer_bodies, answer_labels = fnc_comp_test(
    os.path.join(data_dir, 'competition_test_stances_unlabeled.csv'),
    os.path.join(data_dir, 'competition_test_bodies.csv')
)

predictions, raw_outputs = model.predict(answer_labels)

list_of_tuples = list(zip(answer_headlines, answer_bodies, predictions))
df = pd.DataFrame(list_of_tuples, columns=['Headline', 'Body ID', 'Stance'])
df['Stance'] = df['Stance'].replace({0: 'agree', 1: 'disagree', 2: 'discuss', 3: 'unrelated'})
df.to_csv('/content/drive/MyDrive/598project/answer.csv', index=False, encoding='utf-8')