#%%
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from functools import reduce

illusion_variations = {
    0: {"originalID": 0, "patches" : 40, 'shiftfactor': 4}, 
    1: {"originalID": 1, "patches" : 40, 'shiftfactor': 8}, 
    2: {"originalID": 2, "patches" : 72, 'shiftfactor': 4}, 
    3: {"originalID": 3, "patches" : 72, 'shiftfactor': 8}, 
    4: {"originalID": 4, "patches" : 56, 'shiftfactor': 4}, 
    5: {"originalID": 5, "patches" : 56, 'shiftfactor': 8}, 
    6: {"originalID": 7, "patches" : 88, 'shiftfactor': 4}, 
    7: {"originalID": 6, "patches" : 88, 'shiftfactor': 8}, 
    8: {"originalID": 8, "patches" : 104, 'shiftfactor': 4},
    9: {"originalID": 9, "patches" : 104, 'shiftfactor': 8} 
}
#%% Create one data table with ids and results
path = 'resultExperiments/results/experiment/'
fragments = []
for file in os.listdir(path):
  fragment = pd.read_json(path + file)
  userid = file.split('.')[0] 
  fragment['userID'] = pd.Series([userid for i in range(len(fragment))])
  fragments.append(fragment)

df = pd.concat(fragments, ignore_index=True)
dfp = df[df.illusionName == 'Popple Illusion'].copy()

#%% Print initial dataFrame
df

#%% Swap ids to correct shiftfactor order
mask_7 = dfp.variationID == 7
mask_6 = dfp.variationID == 6
dfp.loc[mask_7, 'variationID'] = 6
dfp.loc[mask_6 , 'variationID'] = 7

#%% Boxplot preparation
fragments = []
for key, val in illusion_variations.items():
    mask = dfp.variationID == key
    fragment = dfp[mask][['userID', 'distortion', 'inverted']].set_index(['userID'])
    fragment.columns = [
      "D-p{}s{}".format(val['patches'], val['shiftfactor']),
      "I-p{}s{}".format(val['patches'], val['shiftfactor'])
    ]
    fragments.append(fragment)

# variation-wise dataset
df_vw = reduce(lambda l, r: l.join(r), fragments[1:], fragments[0])

#%% Print userID DataFrameiloc[:,:10]
df_vw

#%% add demographics to data
path = 'resultExperiments/results/questionnaire/'
for user_id in df_vw.index:
  questionnaire = pd.read_json('{}{}.json'.format(path, user_id), typ='series')
  df_vw.loc[user_id, 'vimp'] = questionnaire['Do you have any visual impairments?']
  df_vw.loc[user_id, 'vimp_type'] = questionnaire['If yes, what and when did you experience these problems?']
  df_vw.loc[user_id, 'other_exp'] = questionnaire['Did you ever participate in an experiment related to perceptual illusions?']
  df_vw.loc[user_id, 'age'] = questionnaire['Age']
  df_vw.loc[user_id, 'gender'] = questionnaire['Gender']

#%% box plot of distortions
df_vw.filter(regex='D-*').boxplot(grid=False)

#%% box plot of distortions
df_vw.filter(regex='I-*').boxplot(grid=False)

#%%
pd.DataFrame([df_vw[c].value_counts() for c in df_vw.filter(regex='I-*')]).transpose()

#%%
df_vw.filter(like='I-p40s8').hist()

#%% age distribution
df_vw['age'].value_counts().plot.bar()

#%%
df_vw['gender'].value_counts().plot.bar()

#%%
df_vw['vimp'].value_counts().plot.bar()

#%% Recreate Multi Histogram
fig, axes = plt.subplots(10,1, figsize=(30, 10))
for id_ax, ax in enumerate(axes.flatten()):
  var = illusion_variations[id_ax]
  ax.set_title('# Patches: {}, Shift Factor: {}'.format(var["patches"], var['shiftfactor']))
  dfp[dfp.variationID == id_ax].distortion.hist(ax=ax, range=(0,1), bins=100)
fig.tight_layout()
#%%
