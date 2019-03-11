import os
import numpy as np

from math import *
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from PIL import Image
from PIL import ImageDraw

staticRsrcFolder = ""

width = 500
height = 500
radius = 200
patches = 60
p = figure()
source = ColumnDataSource()

def init(_staticRsrcFolder):
    """This function will be called before the start of the experiment
    and can be used to initialize variables and generate static resources
    
    :param _staticRsrcFolder: path to a folder where static resources can be stored
    """
    global staticRsrcFolder, p, source
    staticRsrcFolder = _staticRsrcFolder


    p = figure(plot_width=width, plot_height=height, x_range=(0, 1), y_range=(0, 1))
    #p.outline_line_color = None
    p.toolbar.active_drag = None
    p.toolbar.logo = None
    p.toolbar_location = None
    p.xaxis.visible = None
    p.yaxis.visible = None
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None

    pilImage = Image.new("L", (width, height), (150))

    npImg = np.empty((width, height), dtype=np.uint8)
    view = npImg.view(dtype=np.uint8).reshape((width, height))
    view[:,:] = np.flipud(np.asarray(pilImage))

    source = ColumnDataSource({'image': [npImg]})
    p.image(image='image', x=0, y=0, dw=1, dh=1, source=source)

def getName():
    "Returns the name of the illusion"

    return "Template Illusion"

def getInstructions():
    "Returns the instructions as a HTML string"
    
    instruction = """
        <p>Focus your attention on <b style=\"color:red\">the red cross</b> in the centre of the image.
        Your task is to change the distort slider until all the polygons appear square. When ... or when
        you can not find a slider position where ... answer the question and press the \"Submit\" button
        below. Complete this task for each of the variations of this illusion listed below and then press \"Save Data\".</p>
    """
    return instruction

def getQuestion():
    "Returns a string with a Yes/No question that checks if the participant sees the illusion inverted"

    return "Does the illusion look inverted?"

def getNumVariations():
    "Returns the number of variations"

    return 3


def getPatch(phase, width, height):
    patch = Image.new("L", (width, height), (0) )
    return patch

def morphCoordinates(distortion, phi):
    originalX = sin(phi)
    originalY = cos(phi)

    shift = 1*(2*distortion - 1) * ((1+cos(4*phi))/2)

    return ((originalX*(1+shift)), (originalY*(1+shift)))


def draw(variationID, distortion):
    """This function generates the optical illusion figure.
    The function should return a bokeh figure of size 500x500 pixels.

    :param variationID: select which variation to draw (range: 0 to getNumVariations()-1)
    :param distortion: the selected distortion (range: 0.0 to 1.0)
    :return handle to bokeh figure that contains the optical illusion
    """

    global p, source

    pilImage = Image.new("L", (width, height), (150))

    dPhi = pi / (patches / 2)
    phi0 = dPhi / 2
    patchsize = int(floor(radius * pi * 2 / patches))



    for i in range(patches):
        phi = phi0 + i * dPhi
        phiDeg = phi * 180 / pi
        patch = getPatch(phi, patchsize, patchsize)
        mask = Image.new('L', patch.size, 255)
        patch = patch.rotate(phiDeg, expand=True)
        mask = mask.rotate(phiDeg, expand=True)
        
        coord = morphCoordinates(distortion, phi)
        pilImage.paste(patch, (width/2 - patch.size[0]/2 + int(round(radius*coord[0])), height/2 - patch.size[1]/2 + int(round(radius*coord[1]))), mask)


    npImg = np.empty((width, height), dtype=np.uint8)
    view = npImg.view(dtype=np.uint8).reshape((width, height))
    view[:,:] = np.flipud(np.asarray(pilImage))
    source.data = {'image': [npImg]}

    return p