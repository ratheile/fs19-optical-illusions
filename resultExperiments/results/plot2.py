#%%
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

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
#%%
path = 'resultExperiments/results/experiment/'
df = pd.concat([pd.read_json(path + file) for file in os.listdir(path)], ignore_index=True)
dfp = df[df.illusionName == 'Popple Illusion']

# Swap ids to correct shiftfactor order
mask_7 = dfp.variationID == 7
mask_6 = dfp.variationID == 6
dfp.loc[mask_7, 'variationID'] = 6
dfp.loc[mask_6 , 'variationID'] = 7


# Boxplot preparation
data = np.zeros((10,37))
for key, val in illusion_variations.items():
   mask = dfp.variationID == 7
   data[key, :] = 



#%%
fig, axes = plt.subplots(10,1, figsize=(25, 10))
for id_ax, ax in enumerate(axes.flatten()):
  var = illusion_variations[id_ax]
  ax.set_title('# Patches: {}, Shift Factor: {}'.format(var["patches"], var['shiftfactor']))
  dfp[dfp.variationID == id_ax].distortion.hist(ax=ax, range=(0,1), bins=100)

fig.tight_layout()
#%%


#%%
