import numpy as np
import os
from bokeh.layouts import widgetbox, column, row, layout
from bokeh.models.widgets import Button, RadioButtonGroup, Select, Slider, TextInput, RadioGroup, Toggle, Div, Paragraph
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, Range1d
from bokeh.models.callbacks import CustomJS
from bokeh.models.sources import ColumnDataSource
import uuid
import json


## here the illusion is imported 
import illusionTemplate as illusion
#import illusionTemplateAlt as illusion
#import threeSquaresIllusion as illusion

## static resource folder
staticRsrcFolder = "illusionApp/static"
if not os.path.exists(staticRsrcFolder):
    os.makedirs(staticRsrcFolder) 

## data output folder
resultsFolder = 'illusionApp/results'
if not os.path.exists(resultsFolder):
    os.makedirs(resultsFolder) 

## generate participant ID
userID = str(uuid.uuid4())

## the order of variations is randomized
randVariationOrder = True
if randVariationOrder:
    permMap = np.random.permutation(illusion.getNumVariations()) #map from selectorID to variationID
    invPermMap = np.argsort(permMap) #map from variationID to selectorID
else:
    permMap = list(range(illusion.getNumVariations()))
    invPermMap = list(range(illusion.getNumVariations()))

## init output data structure
distortionData = [{'variationID': i, 'selectorID': invPermMap[i], 'submitted': False, 'distortion': None, 'inverted': False} for i in range(illusion.getNumVariations())]


## Create various gui widgets
distortion_slider = Slider(start=0, end=1, step=0.001, value=0.5, show_value=False, tooltips=False)

def reset_slider(): 
    # randomize slider min, max and starting value for every illusion switch 
    # (to avoid the subject remembering the values from previously completed illusion variations)
    distortion_slider.start = np.random.uniform(0, 0.2)
    distortion_slider.end = np.random.uniform(0.8, 1)
    distortion_slider.value = np.random.uniform(distortion_slider.start, distortion_slider.end)

reset_slider()

variation_selector = RadioButtonGroup(labels=list(map(str,np.arange(1,illusion.getNumVariations()+1))), active=0, width=500)

radio_group = RadioGroup( labels=["No", "Yes"], active=0, inline=True, width=200)

submit_button = Button( label='Submit', width=140, button_type = "default")

save_button = Button( label='Save Data', width=140, button_type = "default", disabled=True)

## init illusion
illusion.init(staticRsrcFolder)
p = illusion.draw(permMap[variation_selector.active], distortion_slider.value)
pBox = row(p)

## create layout
layout = column(Div(text="<h2>{}</h2>".format(illusion.getName()), width=500), row(column(
    row(Paragraph(text="User ID:", width=100), Paragraph(text=userID, width=400)),
    row(Paragraph(text="Instruction:", width=100), Div(text=illusion.getInstructions(), width=400)),
    row(Paragraph(text="Variation:", width=100), variation_selector),
    row(Paragraph(text="Distort:", width=100), distortion_slider),
    row(Paragraph(text=illusion.getQuestion(), width=200), radio_group),
    submit_button,
    save_button, width=600), pBox))


## set callbacks
def submit_button_cb():
    distortionData[permMap[variation_selector.active]]['submitted'] = True
    distortionData[permMap[variation_selector.active]]['distortion'] = distortion_slider.value
    distortionData[permMap[variation_selector.active]]['inverted'] = bool(radio_group.active)
    submit_button.button_type = "success"
    submit_button.label =  "Submitted. Again?"

    #activate save_button if all variations were submitted
    if all([l['submitted'] for l in distortionData]):
        save_button.disabled = False

def save_button_cb():
    def default(o):
        if isinstance(o, np.int64): return int(o)  
        raise TypeError

    #print(json.dumps(distortionData, default=default))
    with open('{}/{}.json'.format(resultsFolder,userID), 'w') as outfile:
        json.dump(distortionData, outfile, default=default)

    save_button.button_type = "success"
    save_button.label =  "Data Saved. Again?"


def selector_cb(attr, old, new):
    if distortionData[permMap[variation_selector.active]]['submitted']:
        submit_button.button_type = "success"
        submit_button.label = "Submitted. Again?"
    else:
        submit_button.button_type = "default"
        submit_button.label = "Submit"

    reset_slider()
    radio_group.active = 0

    # call draw function and put the new figure in the layout
    p = illusion.draw(permMap[variation_selector.active], distortion_slider.value)
    pBox.children[0] = p

def slider_cb(attr, old, new):
    # call draw function and put the new figure in the layout
    p = illusion.draw(permMap[variation_selector.active], distortion_slider.value)
    pBox.children[0] = p

submit_button.on_click(submit_button_cb)
variation_selector.on_change('active', selector_cb)

save_button.on_click(save_button_cb)

#slider.on_change('value', cb)
# hack to throttle slider callback (https://stackoverflow.com/questions/38375961/throttling-in-bokeh-application/38379136#38379136)
distortion_slider.callback_policy = 'mouseup' #call only on mouseup
#slider.callback_throttle = 50 #call max every x ms
source = ColumnDataSource(data=dict(value=[]))
source.on_change('data', slider_cb) 
distortion_slider.callback = CustomJS(args=dict(source=source), code="""
    source.data = { value: [cb_obj.value] }
""")

# ## some CSS to center layout
# header = Div(text="""
#     <style>
#     body { width: 1150px; margin: 0 auto; }
#     </style>
# """)
# curdoc().add_root(header)

curdoc().add_root(layout)
curdoc().add_root(source)




