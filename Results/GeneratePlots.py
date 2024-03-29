#%%
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from functools import reduce
from scipy import stats
import seaborn as sns

plt.style.use('seaborn-white')

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
path = 'Results/Data/experiment/'
fragments = []
for file in os.listdir(path):
  fragment = pd.read_json(path + file)
  userid = file.split('.')[0] 
  fragment['userID'] = pd.Series([userid for i in range(len(fragment))])
  fragments.append(fragment)

df = pd.concat(fragments, ignore_index=True)
dfp = df[df.illusionName == 'Popple Illusion'].copy()
dfp
#%% Correct distortion to be in % of radius 
dfp['distortion'] = dfp['distortion'] * 0.2 - 0.1
#%% Print initial dataFrame
dfp

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
path = 'Results/Data/questionnaire/'
for user_id in df_vw.index:
  questionnaire = pd.read_json('{}{}.json'.format(path, user_id), typ='series')
  df_vw.loc[user_id, 'vimp'] = questionnaire['Do you have any visual impairments?']
  df_vw.loc[user_id, 'vimp_type'] = questionnaire['If yes, what and when did you experience these problems?']
  df_vw.loc[user_id, 'other_exp'] = questionnaire['Did you ever participate in an experiment related to perceptual illusions?']
  df_vw.loc[user_id, 'age'] = questionnaire['Age']
  df_vw.loc[user_id, 'gender'] = questionnaire['Gender']

#%% box plot of distortions
fig, ax = plt.subplots(1, 1, figsize=(15,10))
df_vw.filter(regex='D-*').boxplot(
        grid=False,
        ax=ax
      )
ax.set_title("Distortion Factor for each Configuration")
fig.savefig('Plots/boxes')

#%% Aggregated boxplots
fig, ax = plt.subplots(1, 1, figsize=(5,7))
bp_aggregated = pd.DataFrame([
    df_vw.filter(regex='D-.*s4').melt()['value'],
    df_vw.filter(regex='D-.*s8').melt()['value']
  ]).transpose()
bp_aggregated.columns = ['s4', 's8']
# bp_aggregated.boxplot(grid=False, ax=ax)
sns.violinplot(data=bp_aggregated)
ax.set_title("distortion w.r.t. shift factor")
fig.savefig('Plots/violin_plot_shift_factor.png')

#%%
bp_aggregated

#%%
fig, ax = plt.subplots(1, 2, figsize=(6,3))
stats.probplot(bp_aggregated['s4'], plot=ax[0])
stats.probplot(bp_aggregated['s8'], plot=ax[1])
ax[0].set_title("Q-Q plot of shift factor 4 data")
ax[1].set_title("Q-Q plot of shift factor 8 data")
fig.tight_layout()
fig.savefig('Plots/qqplot.png')


#%% Perform a shapiro / kstest test on shift factor data
print(stats.shapiro(bp_aggregated['s4']))
print(stats.shapiro(bp_aggregated['s8']))
print(stats.kstest(bp_aggregated['s4'], 'norm'))
print(stats.kstest(bp_aggregated['s8'], 'norm'))

print(stats.ttest_ind(bp_aggregated['s4'], bp_aggregated['s8']))
print(bp_aggregated.kurtosis())

print(stats.ttest_1samp(bp_aggregated, 0.0))


#%% Aggregated boxplots
fig, ax = plt.subplots(1, 1, figsize=(5,10))
bp_patches = pd.DataFrame([
    df_vw.filter(regex='D-p40*').melt()['value'],
    df_vw.filter(regex='D-p56*').melt()['value'],
    df_vw.filter(regex='D-p72*').melt()['value'],
    df_vw.filter(regex='D-p88*').melt()['value'],
    df_vw.filter(regex='D-p104*').melt()['value']
  ]).transpose()
bp_patches.columns = ['p40', 'p56', 'p72', 'p88', 'p104']
# bp_aggregated.boxplot(grid=False, ax=ax)
sns.violinplot(data=bp_patches)
ax.set_title("Aggregated Distortion over all Shiftfactors")
fig.savefig('Plots/aggregated_boxes_size')

#%%
columns = ['p40', 'p56', 'p72', 'p88', 'p104']
s4 = df_vw.filter(regex='D-.*s4').copy().melt(
  var_name='patches', value_name='distortion')
s8 = df_vw.filter(regex='D-.*s8').copy().melt(
  var_name='patches', value_name='distortion')
s4['patches'] = s4['patches'].apply(lambda v: v[:-2])
s8['patches'] = s8['patches'].apply(lambda v: v[:-2])
s4['shift'] = 4 
s8['shift'] = 8 
bp_patches_long = pd.concat(
  [s4, s8]
)
fig, ax = plt.subplots(1, 1, figsize=(5,7))

# bp_aggregated.boxplot(grid=False, ax=ax)
sns.violinplot(x='patches', y='distortion',
  data=bp_patches_long,
  split=True,
  order=['D-'+c for c in columns],
  inner='quartile',
  hue='shift')
ax.set_title("aggregated distortion over all # of patches ")
fig.tight_layout()
fig.savefig('Plots/violin_plot_patch_size.png')

#%%
fig, ax = plt.subplots(1, 1, figsize=(5,3))
d_mean = []
for c in columns:
  p4 = bp_patches_long[
    (bp_patches_long['patches'] == 'D-{}'.format(c)) &
    (bp_patches_long['shift'] == 4)
  ]
  p8 = bp_patches_long[
    (bp_patches_long['patches'] == 'D-{}'.format(c)) &
    (bp_patches_long['shift'] == 8)
  ]
  d_mean.append([
    p4['distortion'].mean(),
    p8['distortion'].mean()]) 
  
d_mean_df = pd.DataFrame(d_mean)
d_mean_df = d_mean_df.set_index(pd.Index(columns))
d_mean_df.columns = [4,8]
ax.set_title('increased influence of sf-8 for small # of patches')
(np.abs(d_mean_df[8] - d_mean_df[4])).plot(ax=ax, marker='o')
ax.set_ylabel('abs(mean(sf = 8) - mean(sf = 4))')
ax.set_xlabel('# of patches')
fig.tight_layout()
fig.savefig('Plots/means_diverge.png')

#%%
fig, axes = plt.subplots(1, 2, figsize=(10,10))

ax = axes[0]
sns.violinplot(x='patches', y='distortion',
    data=bp_patches_long,
    split=True,
    ax=ax,
    order=['D-p40', 'D-p56', 'D-p72', 'D-p88', 'D-p104'],
    hue='shift'
  )

ax = axes[1]
bp_patches.boxplot(grid=False, ax=ax)


#%% Stat analysis of # patches
p_vals = np.zeros((5,5))
for id_x, col in enumerate(bp_patches):
  print(stats.shapiro(bp_patches[col]))
  print(stats.kstest(bp_patches[col], 'norm'))
  # stats.probplot(bp_aggregated[col], plot=ax)
  for id_y, row in enumerate(bp_patches):
    p_vals[id_y, id_x] = stats.ttest_ind(
      bp_patches[col],
      bp_patches[row]
    ).pvalue

print(stats.ttest_1samp(bp_patches, 0.0))

p_val_df = pd.DataFrame(p_vals)
p_val_df = p_val_df.set_index(pd.Index(bp_patches.columns))
p_val_df.columns = bp_patches.columns

fig, ax = plt.subplots(1, 1, figsize=(3,3))
plot = ax.matshow((p_val_df < 0.05).astype(int), cmap='RdYlGn')
ax.set_title('pairwise t-test: p-value < 0.05')
ax.set_xticklabels(bp_patches.columns)
ax.set_yticklabels(bp_patches.columns)
ax.set_xticks(np.arange(len(bp_patches.columns)))
ax.set_yticks(np.arange(len(bp_patches.columns)))
ax.set_facecolor('white')
fig.tight_layout()
fig.savefig('Plots/ttest_patch_size_matrix.png')


#%% box plot of distortions
df_vw.filter(regex='I-*').boxplot(grid=False)
df_vw.filter(regex='I-*').mean().mean()

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
fig, axes = plt.subplots(10,1, figsize=(5, 15))
for id_ax, ax in enumerate(axes.flatten()):
  var = illusion_variations[id_ax]
  ax.set_title('# Patches: {}, Shift Factor: {}'.format(var["patches"], var['shiftfactor']))
  data = dfp[dfp.variationID == id_ax].distortion
  data.hist(ax=ax, range=(-0.1,0.1), bins=100, density=True)
  r = np.arange(-0.1, 0.1, 0.001)
  ax.plot(r, stats.norm.pdf(r, data.mean(), data.std()))
  ax.set_xlim(-0.05, 0.05)
fig.tight_layout()
fig.savefig('Plots/distribution')
#%%
data.mean()
data.std()

#%%
tips = sns.load_dataset("tips")

#%%
tips

#%%
