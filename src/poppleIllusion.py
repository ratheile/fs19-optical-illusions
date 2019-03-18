import os
import io
import numpy as np

import cv2
from math import *
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from PIL import Image
from PIL import ImageOps
from PIL import ImageDraw

width = 1000
height = 1000
radius = 450
patches = 60

downsampled_width = 500
downsampled_height = 500

enableCheat = False

p = figure()
source = ColumnDataSource()

illusion_variations = {
    0: {"originalID": 0, "patches" : 72, 'shiftfactor': 16}, 
    1: {"originalID": 1, "patches" : 72, 'shiftfactor': 8}, 
    2: {"originalID": 2, "patches" : 40, 'shiftfactor': 16}, 
    3: {"originalID": 3, "patches" : 40, 'shiftfactor': 8}, 
    4: {"originalID": 4, "patches" : 40, 'shiftfactor': 4}, 
    5: {"originalID": 5, "patches" : 72, 'shiftfactor': 4}, 
    6: {"originalID": 6, "patches" : 96, 'shiftfactor': 16}, 
    7: {"originalID": 7, "patches" : 96, 'shiftfactor': 8}, 
    8: {"originalID": 8, "patches" : 96, 'shiftfactor': 64} 
}


staticRsrcFolder = ""

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

    pilImage = Image.new('RGBA', (width, height), (150,150,150,255))

    npImg = np.empty((width, height), dtype=np.uint32)
    view = npImg.view(dtype=np.uint8).reshape((width, height,4))
    view[:,:] = np.flipud(np.asarray(pilImage))

    source = ColumnDataSource({'image': [npImg]})
    p.image_rgba(image='image', x=0, y=0, dw=1, dh=1, source=source)


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

    return len(illusion_variations)


def getPatch(phase, width, height):
    patch = Image.new("L", (width, height), (0) )
    return patch

def cheat():
    global enableCheat
    enableCheat = not enableCheat

def morphCoordinates(distortion, phi):
    originalX = cos(phi)
    originalY = sin(phi)

    amount = 0.1

    shift = amount*(2*distortion - 1) * ((cos(4*phi)))

    rotCorr = phi + 4 * amount * (2*distortion - 1) * ((sin(4*phi)))

    return ((originalX*(1+shift)), (originalY*(1+shift)), rotCorr*180/pi)


def gabor_patch(size, psi):

    oversample_ratio = 1
    theta = 0.0
    blur_ratio = 2

    size = size * oversample_ratio
    sigma = size/6
    lambd = size

    kern = cv2.getGaborKernel(
      (size, size),
      sigma, theta, lambd, 0.5, psi, ktype=cv2.CV_32F
    )

    cv2.blur(kern, (int(size / blur_ratio), int(size / blur_ratio)))

    if oversample_ratio > 1:
        return cv2.resize(
            kern, 
            (int(size / oversample_ratio) , int(size / oversample_ratio))
        )
    else:
        return kern

def draw(variationID, distortion):
    """This function generates the optical illusion figure.
    The function should return a bokeh figure of size 500x500 pixels.

    :param variationID: select which variation to draw (range: 0 to getNumVariations()-1)
    :param distortion: the selected distortion (range: 0.0 to 1.0)
    :return handle to bokeh figure that contains the optical illusion
    """

    global p, source

    pilImage = Image.new("RGBA", (width, height), (125,125,125,255))

    patches = illusion_variations[variationID]['patches']
    factor = illusion_variations[variationID]['shiftfactor']

    dPhi = pi / (patches / 2)
    phi0 = 0# dPhi / 2
    patchsize = int(floor(radius * pi * 2 / patches))
    direction = 1
    patchPhi = 0

    for i in range(int(patches)):
        phi = phi0 + i * dPhi
        patchPhi =  direction * (factor * i * dPhi) + phi0

        if i % (int(patches/8)) == 0:
            direction *= -1

        patch_mat = gabor_patch(patchsize, patchPhi)
        patch_mat = np.interp(patch_mat, (-1, 1), (0, 255))
        patch = Image.fromarray(np.uint8(patch_mat))

        coord = morphCoordinates(distortion, phi)
        mask = Image.new('L', patch.size, 255)
        patch = patch.rotate(-coord[2], expand=True, resample=Image.BICUBIC)
        mask = mask.rotate(-coord[2], expand=True, resample=Image.BICUBIC)
        
        pilImage.paste(
            patch,
            ( # the box parameter
                int(width/2  - patch.size[0]/2 + int(round(radius*coord[0]))),
                int(height/2 - patch.size[1]/2 + int(round(radius*coord[1])))
            ),
            mask
        )

    draw = ImageDraw.Draw(pilImage)
    if enableCheat:
        draw.ellipse(
            [
                (width*0.5 - radius, height*0.5 - radius), 
                (width*0.5 + radius, height*0.5 + radius)
            ], 
            outline=(255,0,0)
        )

    draw.line([width/2, height/2 - 10, width/2, height/2 + 10], fill=(255,0,0), width=1)
    draw.line([width/2 - 10, height/2, width/2 + 10, height/2], fill=(255,0,0), width=1)

    del draw
    
    npImg = np.empty((width, height), dtype=np.uint32)
    view = npImg.view(dtype=np.uint8).reshape((width, height, 4))
    view[:,:] = np.flipud(np.asarray(pilImage))

    print(distortion)

    source.data = {'image': [npImg]}
    return p