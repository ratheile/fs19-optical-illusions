#**************************************************************************
# Program name      : IllusionApp - Popple Illusion
# Authors           : Jonathan Kakon, Raffael Thieler,
#                     Jannis Schönleber, Marina Morisod
# Date created      : 11.03.2019
# Last edited       : 29.07.2019
# Revision          : 1
# Usage             : In conjuncture with main.py;
#                     (python(3)) bokeh serve ./
#**************************************************************************

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

# default parameters
width = 500
height = 500
radius = 200
patches = 60

downsampled_width = 500
downsampled_height = 500

enableCheat = False

# create a figure and a Datasource to enable faster image updating
p = figure()
source = ColumnDataSource()

# Illusion variations. 
#   paches: number of patches around the circle.
#   shiftfactor: amount of phase shift from one gabor patch to the next.
illusion_variations = {
    0: {"originalID": 0, "patches" : 40, 'shiftfactor': 4}, 
    1: {"originalID": 1, "patches" : 40, 'shiftfactor': 8}, 
    2: {"originalID": 2, "patches" : 72, 'shiftfactor': 4}, 
    3: {"originalID": 3, "patches" : 72, 'shiftfactor': 8}, 
    4: {"originalID": 4, "patches" : 56, 'shiftfactor': 4}, 
    5: {"originalID": 5, "patches" : 56, 'shiftfactor': 8}, 
    6: {"originalID": 6, "patches" : 88, 'shiftfactor': 8}, 
    7: {"originalID": 7, "patches" : 88, 'shiftfactor': 4}, 
    8: {"originalID": 8, "patches" : 104, 'shiftfactor': 4},
    9: {"originalID": 9, "patches" : 104, 'shiftfactor': 8} 
}


def init(_staticRsrcFolder):
    """This function will be called before the start of the experiment
    and can be used to initialize variables and generate static resources
    
    :param _staticRsrcFolder: path to a folder where static resources can be stored
    """
    global p, source

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

    return "Popple Illusion"

def getInstructions():
    "Returns the instructions as a HTML string"
    
    instruction = """
        <p>Focus your attention on <b style=\"color:red\">the red cross</b> in the centre of the image.
        Your task is to change the distort slider until the surrounding illusion appears completely circular.
        </p>
    """
    return instruction

def getQuestion():
    "Returns a string with a Yes/No question that checks if the participant sees the illusion inverted"

    return "Could you get rid of the disortion?"

def getNumVariations():
    "Returns the number of variations"

    return len(illusion_variations)

def cheat():
    "Used to cheat during development. Draws a red circle inside the illusion."
    global enableCheat
    enableCheat = not enableCheat

def morphCoordinates(distortion, phi):
    """Modulates x and y coordinates according to a distortion value between 0 and 1.
    
    :param distortion:  amplitude factor of the cosine radius modulation (+- 10% of radius)
    :param phi:         angular location of the patch to be moved.

    :returns tripplet containing (xshift, yshift, rotationCorrection)
    xshift: factor for the x coordinate.
    yshift: factor for the y coordinate.
    rotationCorrection: angle to rotate the patch to line up with the adjacent ones.
    """

    # standard circle coordinates.
    originalX = cos(phi) 
    originalY = sin(phi)

    amount = 0.1

    # shift factor along the radial direction modulated by cos(4*phi)
    shift = amount*(2*distortion - 1) * ((cos(4*phi)))

    # rotation correction: dshift/dphi to align the patch tangentially with the modulated circle
    rotCorr = phi + 4 * amount * (2*distortion - 1) * ((sin(4*phi)))

    # return aggregate.
    return ((originalX*(1+shift)), (originalY*(1+shift)), rotCorr*180/pi)


def gaborPatch(size, psi, lambda_mult=1):
    """
        Generates a gabor patch with fixed sigma/lamda of 1/6, theta of 0 
        and blurrs it further to create a smoother transition to the background.

        :param size:    size of the gabor patch (width and height)
        :param psi:     phase shift of the gabor function
        :param lambda_mult: parameter to change the sigma/lambda ratio. not used in current Implementation

        :returns a Gabor Patch of size (size, size) blurred at the edges.
    """

    # fixed parameters
    oversample_ratio = 1
    theta = 0.0
    blur_ratio = 2
    size = size * oversample_ratio
    sigma = size/6
    lambd = size/lambda_mult

    # OpenCV2 Gabor Kernel generation
    kern = cv2.getGaborKernel(
      (size, size),
      sigma, theta, lambd, 0.5, psi, ktype=cv2.CV_32F
    )

    # Blur the kernel
    cv2.blur(kern, (int(size / blur_ratio), int(size / blur_ratio)))

    # Eventually resample after an oversampled generation and return the patch.
    if oversample_ratio > 1:
        return cv2.resize(
            kern, 
            (int(size / oversample_ratio) , int(size / oversample_ratio))
        )
    else:
        return kern

def draw(variationID, distortion, shift_override=None, patch_override=None, lambda_override=None):
    """This function generates the optical illusion figure.
    The function should return a bokeh figure of size 500x500 pixels.

    :param variationID: select which variation to draw (range: 0 to getNumVariations()-1)
    :param distortion: the selected distortion (range: 0.0 to 1.0)
    :return handle to bokeh figure that contains the optical illusion
    """

    # use the previously defined source to update the illusion without recreating a new figure.
    global p, source

    # base image with a medium gray background.
    pilImage = Image.new("RGBA", (width, height), (125,125,125,255))

    #Sliders for debug purposes
    if lambda_override is not None:
        print("Overriding the lambda frequency multiplier: {}".format(lambda_override))
        illusion_variations[variationID]['lambda_multiplier'] = lambda_override

    lambda_multiplier = 1
    if 'lambda_multiplier' in illusion_variations[variationID]:
        lambda_multiplier = illusion_variations[variationID]['lambda_multiplier']

    if patch_override is not None:
        print("Overriding number of patches: {}".format(patch_override))
        patches = patch_override*8
        illusion_variations[variationID]['patches'] = patches
    else:
        patches = illusion_variations[variationID]['patches']

    if shift_override is not None:
        print("Overriding shift: {}".format(shift_override))
        factor = shift_override*8
        illusion_variations[variationID]['shiftfactor'] = factor
    else: 
        factor = illusion_variations[variationID]['shiftfactor']

    # angular step for the patch placement
    dPhi = pi / (patches / 2)
    phi0 = 0# dPhi / 2
    # calculation of the patch size to fit into a same size circle every time
    patchsize = int(floor(radius * pi * 2 / patches))
    # starting direction of the phase step between gabor patches
    direction = 1
    # starting patch phase shift
    patchPhi = 0


    # Loop to place all patches in a circular manner with the distortion applied.
    for i in range(int(patches)):
        # Increment angle
        phi = phi0 + i * dPhi
        # increment Patch phaseshift.
        patchPhi =  direction * (factor * i * dPhi) + phi0

        # flip Patch phase shift if threshold reached.
        if i % (int(patches/8)) == 0:
            direction *= -1

        # generate Gabor Patch matrix and create a PIL Image from it.
        patch_mat = gaborPatch(patchsize, patchPhi, lambda_multiplier)
        patch_mat = np.interp(patch_mat, (-1, 1), (0, 255))
        patch = Image.fromarray(np.uint8(patch_mat))

        # calculate modified coordinates.
        coord = morphCoordinates(distortion, phi)
        mask = Image.new('L', patch.size, 255)
        # rotate patch to align tangentially with the modulated circle
        patch = patch.rotate(-coord[2], expand=True, resample=Image.BICUBIC)
        mask = mask.rotate(-coord[2], expand=True, resample=Image.BICUBIC)
        
        # place the patch on the base Image with the modified X,Y coordinates
        pilImage.paste(
            patch,
            ( # the box parameter
                int(width/2  - patch.size[0]/2 + int(round(radius*coord[0]))),
                int(height/2 - patch.size[1]/2 + int(round(radius*coord[1])))
            ),
            mask
        )

    # draw a red circle if cheat is enabled. (Debug purposes)
    draw = ImageDraw.Draw(pilImage)
    if enableCheat:
        draw.ellipse(
            [
                (width*0.5 - radius, height*0.5 - radius), 
                (width*0.5 + radius, height*0.5 + radius)
            ], 
            outline=(255,0,0)
        )

    # add a cross in the center of the Image for the participants to focus on.
    draw.line([width/2, height/2 - 10, width/2, height/2 + 10], fill=(255,0,0), width=1)
    draw.line([width/2 - 10, height/2, width/2 + 10, height/2], fill=(255,0,0), width=1)

    # free draw Object
    del draw
    
    # Convert Image to a bokeh figure readable format
    npImg = np.empty((width, height), dtype=np.uint32)
    view = npImg.view(dtype=np.uint8).reshape((width, height, 4))
    view[:,:] = np.flipud(np.asarray(pilImage))

    # update the Data Source
    source.data = {'image': [npImg]}

    # return the figure
    return p