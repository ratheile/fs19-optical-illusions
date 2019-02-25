import os
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import NullLocator
from PIL import Image
from matplotlib.backends.backend_agg import FigureCanvasAgg

from bokeh.io import show
from bokeh.layouts import widgetbox, column, row, layout
from bokeh.models.widgets import Button, RadioButtonGroup, Select, Slider, TextInput, RadioGroup, Toggle, Div
from bokeh.plotting import figure, curdoc
from bokeh.models.plots import Plot
from bokeh.models import ColumnDataSource, Range1d
from itertools import islice
from bokeh.models.callbacks import CustomJS
from bokeh.models.sources import ColumnDataSource


## Illusion parameters (default values) 
# Image scale of the illusion 
default_image_scale = 5
# density of the lines in the square pattern
default_density = 4 
# the line width of the purple square
default_purple_width = 2 
# Distortion we will apply to the purple squares 
default_distort = 0. 
# line width of the black lines in the pattern  
default_pattern_linewidth = 1.8 
# Hatch sets the hatching pattern in a Matplotlib patch. hatch can be one of: 
# [‘/’ | ‘\’ | ‘|’ | ‘-‘ | ‘+’ | ‘x’ | ‘o’ | ‘O’ | ‘.’ | ‘*’]
# Which fills a matplotlib patch with a different pattern. 
default_hatch_1 = "/"
# 
default_hatch_2 = "\\"
# The distance between all outer and inner squares. This is a relative value. 
dist = 1. 
# The width of a single square. 
pattern_square_width = dist * 8 - dist


# Folder where background images are stored
staticRsrcFolder = ""
pattern_folder = ""

    
# If true, will keep redrawing pattern every time a user interacts with the illusion 
force_replot = False 

default_parameters = {
    "image_scale": default_image_scale, 
    "density": default_density, 
    "purple_width": default_purple_width, 
    "pattern_linewidth": default_pattern_linewidth, 
    "hatch_1": default_hatch_1, 
    "hatch_2": default_hatch_2, 
    "pattern_angle": None, # Apply a rotation to the lines in the background pattern. 
    "originalID": None # Represents the actual ID of our illusion. 
}

## This variable specifies the parameter variations we will apply 
illusion_variations = {
    1: {"originalID": 1}, 
    2: {"hatch_1": "\\", "hatch_2": "/", "originalID": 2}, 
    3: {"density": 2, "originalID": 3}, 
    4: {"hatch_1": "|", "hatch_2": "-", "originalID": 4}    
}

# Angle variations we will look at: from 10 to 80 degrees 
angles = range(10, 90, 10)

remaining_indices = range(max(illusion_variations.keys()) + 1, len(angles) + max(illusion_variations.keys()) + 1)
for i, ang in zip(remaining_indices, angles): 
    illusion_variations[i] = {"pattern_angle": ang, "originalID": i}
    
llusion_count = len(illusion_variations)
## This dictionary contains the final illusion parameters for each illusion variation we will 
# display to the subject. 
illusion_variation_dict = {}
illusions_to_modify = list(illusion_variations.keys())

# Create a dictionary with default parameters
for i in illusions_to_modify: 
    illusion_variation_dict[i] = default_parameters.copy()

# Modify the parameters according to our illusion variations 
for variationId, variation in illusion_variations.items(): 
    for key, value in variation.items(): 
        illusion_variation_dict[variationId][key] = value


# Make sure number of illusions adds up
#assert not illusions_to_modify

def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = np.fromstring ( fig.canvas.tostring_argb(), dtype=np.uint8 )
    buf.shape = ( w, h,4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = np.roll ( buf, 3, axis = 2 )
    return buf

########################################################################
## Simple implementation of the background pattern. 
def get_patches(x, y, dist, hatch_size, hatch_1="/", hatch_2="\\"): 
    """Draw a single background square, that itself consists of 3 individual squares, filled with lines. 
    
    :param x: x location to place the square
    :param y: y location to place the square 
    :param dist: 
    :param hatch_size: density of the lines in the pattern 
    :param hatch_1: orientation of the lines in the outer most square in the pattern. 
    This is a feature of matplotlib, "\\" will draw lines from top left to bottom right, 
    while "/" will draw them from top right to bottom left. 
    :param hatch_2: 
    :return: an array of patches 
    """
    patches_arr = [] 
    curr_hatch = hatch_size * hatch_1
    sizes = np.arange(dist, dist*8, dist*2)[::-1]
    for current_size in sizes: 
        # Generate a square at the desired location (x, y) with size current_size. Fill it with line pattern. 
        p = patches.Rectangle(
                (x, y), current_size, current_size,
                hatch=curr_hatch, 
                fill=True, 
                facecolor="white", 
                edgecolor='black', 
                lw=0, 
                zorder=0
            )
        patches_arr.append(p)
        x += dist 
        y += dist 
        if curr_hatch[0] == hatch_1: 
            curr_hatch = hatch_size * hatch_2
        else: 
            curr_hatch = hatch_size * hatch_1
    return patches_arr


def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result    
    for elem in it:
        result = result[1:] + (elem,)
        yield result

## More complex implementation of the pattern. 
# Allows to specify the angle of the black lines.

def plot_hatches(filename, angle, offset=.05, linewidth=4, figsize=(2.4, 2.4), dpi=150):
    """"Generate striped pattern, and save as .png. 
    
    :param filename: the filename to save the pattern to
    :param angle: the angle of the lines 
    :param offset: the distance between the lines
    :param linewidth: the width of the liens 
    :param figsize: the size of the saved image
    :param dpi: the dpi of the image"""
    fig = plt.figure(figsize=figsize, dpi=dpi, frameon=False)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ## Generate lines at an angle 
    angle_radians = np.radians(angle)
    x = np.linspace(-2, 2, 10)
    for c in np.arange(-2, 2, offset):
        yprime = np.cos(angle_radians) * c + np.sin(angle_radians) * x
        xprime = np.sin(angle_radians) * c - np.cos(angle_radians) * x
        ax.plot(xprime, yprime, color="black", linewidth=linewidth)
        
    # Remove as much whitespace around plot as possible. 
    ax.set_ylim(0., 1.)
    ax.set_xlim(0., 1.)
    a=fig.gca()
    a.set_frame_on(False)
    a.set_xticks([])
    a.set_yticks([])
    plt.axis('off')
    ax.axis('off')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    plt.savefig(filename, bbox_inches="tight", pad_inches=0)
    plt.clf()
    plt.close()

def plot_pattern(angle, size=pattern_square_width, offsets=[0.03, 0.05, 0.08, 0.21], linewidth=8., linewidth_step=1., dpi=100, force_replot=force_replot):
    """Combine striped patterns to get our illusion background
    
    :param angle: the angle of the lines 
    :param size: the size of the figure
    :param offsets: the space between the lines for each pattern (manually determined, depend on the image scale)
    :param linewidth: the thickness of the line 
    :param linewidth_step: increase the line thickness by this amount for every smaller pattern
    :param dpi: the dpi of the output image
    :param force_replot: if true, will redraw the pattern every time, otherwise load from disc 
    
    :return: list of filenames that contain the patterns"""
    size_step = size / 4
    filenames = []
    angle_1 = angle 
    angle_2 = 90 + angle 
    for i in range(1,5):
        filename = "{}/hatch_background_{}_{}.png".format(pattern_folder, i, angle)
        if not os.path.isfile(filename) or force_replot: # If already generated this angle 
            plot_hatches(filename, angle, offset=offsets[i-1], linewidth=linewidth, figsize=(size, size), dpi=dpi)    
        linewidth += linewidth_step
        # Decrease size of figure
        size -= size_step
        # Alternate the angle 
        angle = angle_1 if angle != angle_1 else angle_2 
        filenames.append(filename)
    return filenames


def distance(a, b): 
    return np.sqrt(np.square(a[1] - a[0]) + np.square(b[1] - b[0]))

def get_distorted_square(start_location, size, line_width=1., distort=0., print_degrees=False, 
                         reverse_distort=False): 
    """Draw a single distorted purple square. 
    
    :param start_location: the distance from the origin of the purple square
    :param size: the size of the square
    :param line_width: width of the square
    :param distort: amount of distortion to be applied to the square
    :param reverse_distort: if true, distort in the opposite direction (e.g. the middle square)
    :return: a Polygon patch that contains the square 
    """
    orig_square_size = distance([start_location, start_location], [start_location, start_location + size])
    # print "Square size: {}".format(orig_square_size)
    
    # Determine the points of the square 
    if reverse_distort: 
        bottom_left_location = [start_location + distort, start_location + distort]
        bottom_right_location = [start_location, start_location + size]
        top_right_location = [start_location + size - distort, start_location + size - distort]
        top_left_location = [start_location + size, start_location]
    else: 
        bottom_left_location = [start_location, start_location]
        bottom_right_location = [start_location + distort, start_location + size - distort]
        top_right_location = [start_location + size, start_location + size]
        top_left_location = [start_location + size - distort, start_location + distort]

    ## Draw a polygon. 
    # Essentially the way this works is you choose four points (x, y), and matplotlib conntects and fills them 
    polygon = patches.Polygon([bottom_left_location, bottom_right_location, 
                            top_right_location, top_left_location], 
                            closed=True, fill=False, 
                            linewidth=str(line_width),
                            edgecolor="purple", 
                              zorder=1)
    
    if print_degrees: 
        # Calculate the angle of the rhombus after applying the distortion
        diagonal1 = distance(top_left_location, bottom_right_location)
        diagonal2 = orig_square_size * np.sqrt(2)
        side = np.sqrt(np.square(diagonal1) + np.square(diagonal2))/2
        area = (diagonal1 * diagonal2) / 2 
        sine_a = area / np.square(side) 
        rhombus_angle = np.degrees(np.arcsin(sine_a))
        # Uncomment to see the angle of the squares
#         print("Rhombus angle: {}".format(rhombus_angle))
        return polygon, rhombus_angle
    else: 
        return polygon


def init(_staticRsrcFolder):
    """This function will be called before the start of the experiment
    and can be used to initialize variables and generate static resources
    
    :param _staticRsrcFolder: path to a folder where static resources can be stored
    """
    global staticRsrcFolder
    staticRsrcFolder = _staticRsrcFolder

    global pattern_folder
    pattern_folder = os.path.join(staticRsrcFolder, "background")
    print(pattern_folder)

    if not os.path.exists(pattern_folder):
        os.makedirs(pattern_folder)

    ## Generate the images of the background pattern in advance, to save computation  
    for d in illusion_variation_dict.values(): 
        angle = d["pattern_angle"]
        if angle is not None: 
            plot_pattern(angle)
            plot_pattern(-angle)


def getName():
    "Returns the name of the illusion"
    return "Three Squares Illusion"

def getInstructions():
    "Returns the instructions as a HTML string"
    
    instruction = """
        <p>Focus your attention on <b style=\"color:red\">the red cross</b> in the centre of the image.
        Your task is to change the distort slider until all the polygons appear square. When they look square or when
        you can not find a slider position where the look square answer the question and press the \"Submit\" button
        below. Complete this task for each of the variations of this illusion listed below and then press \"Save Data\".</p>
    """
    return instruction

def getQuestion():
    "Returns a string with a Yes/No question that checks if the participant sees the illusion inverted"

    return "Do the squares appear straight?"


def getNumVariations():
    "Returns the number of variations"
    return llusion_count


def draw(variationID, distortion):
    """This function generates the optical illusion figure.
    The function should return a bokeh figure of size 500x500 pixels.

    :param variationID: select which variation to draw (range: 0 to getNumVariations()-1)
    :param distortion: the selected distorion (range: 0.0 to 1.0)
    :return handle to bokeh figure that contains the optical illusion
    """

    illusion_selector = variationID+1
    distort = (distortion*2-1)*0.15

    ## Create bokeh figure and disable axes and tools
    bokehFig = figure(plot_width=500, plot_height=500, x_range=(0, 1), y_range=(0, 1))
    #p.outline_line_color = None
    bokehFig.toolbar.active_drag = None
    bokehFig.toolbar.logo = None
    bokehFig.toolbar_location = None
    bokehFig.xaxis.visible = None
    bokehFig.yaxis.visible = None
    bokehFig.xgrid.grid_line_color = None
    bokehFig.ygrid.grid_line_color = None

    # Load the parameters for the selected illusion 
    params_dict = illusion_variation_dict[illusion_selector]    
    img_scale = params_dict["image_scale"]
    pattern_linewidth = params_dict["pattern_linewidth"]
    density = params_dict["density"]
    purple_width = params_dict["purple_width"]
    hatch_1 = params_dict["hatch_1"]
    hatch_2 = params_dict["hatch_2"]
    pattern_angle = params_dict["pattern_angle"]
    originalID = params_dict["originalID"]
#     print(pattern_angle)

    ### Draw the nine background squares 
    # The width of the line of the pattern. This is a parameter of Matplotlib. 
    matplotlib.rcParams['hatch.linewidth'] = pattern_linewidth
    # Container for all the elements to be drawn 
    patches_arr = []
    sizes = np.arange(0., pattern_square_width * 3, pattern_square_width)
    h1 = hatch_1
    h2 = hatch_2
        
    if pattern_angle is None: # If we don't need an angle applied to the background pattern
        # Draw the 3x3 pattern: simple version 
        for size_1 in sizes: 
            for size_2 in sizes: 
                patches_arr += get_patches(size_1, size_2, dist, density, hatch_1=h1, hatch_2=h2)
                if h1 == hatch_2:                
                    h1 = hatch_1
                    h2 = hatch_2
                else: 
                    h1 = hatch_2
                    h2 = hatch_1
                
    ### Draw the three purple squares
    # The location of the purple square
    purple_loc = pattern_square_width + dist / 2
    # the size of the square 
    current_size = pattern_square_width - dist
    # Uncomment to see the value of the distortion
#     print("Distort input: {}".format(distort))
    purple_patches = []
    for i in range(3): 
        # Make distortion proportional to the size of the square 
        distort_ = distort * current_size
        # print "Distort value for square {}: {}".format(i + 1, distort_)
        if i == 0: 
            square, rhombus_degrees = get_distorted_square(purple_loc, current_size, purple_width,distort_, 
                                            print_degrees=True, reverse_distort=False)
            purple_patches.append(square)
        elif i == 1: # Distort middle square in the opposite direction 
            purple_patches.append(get_distorted_square(purple_loc, current_size, purple_width,distort_, 
                                            print_degrees=False, reverse_distort=True))
        else: 
            purple_patches.append(get_distorted_square(purple_loc, current_size, purple_width,distort_, 
                                            reverse_distort=False))
        # Update location and size for the next square to be drawn 
        purple_loc += dist
        current_size -= dist * 2 
    
    ### Render final figure 
    fig = plt.figure(figsize=(img_scale,img_scale), dpi=100)
    #ax = fig.add_subplot(111,  aspect='equal')
    # fig = plt.figure(figsize=(img_scale,img_scale), dpi=100, frameon=False)
    ax = fig.add_axes([0, 0, 1, 1])
    
    if pattern_angle is None : 
        for p in patches_arr:
            # add_patch adds a patch to the current figure 
            ax.add_patch(p)
            
    else: 
        ## Draw the 3x3 background pattern: more complicated version         
        def display_single_pattern(size_1, size_2, hatches): 
            """Plot a single square of the pattern
            
            :param size_1, size_2: starting coordinates of this plot"""
            a, b, c, d = size_1[0], size_1[1], size_2[0], size_2[1]
            for i in range(4): 
                img = Image.open(hatches[i])
                width, height = img.size
                # Crop the image with PIL library, because Matplotlib adds a little white border
                img = img.crop((3, 3, width - 3, height - 3))
                plt.imshow(img, interpolation="none", aspect="equal", extent=(a, b, c, d), origin='upper')
                a += dist
                b -= dist 
                c += dist
                d -= dist
        
        # Get the list of patterns (redraw or from disk)
        hatches_1 = plot_pattern(pattern_angle)
        hatches_2 = plot_pattern(-pattern_angle)
        
        sizes = np.arange(0., pattern_square_width * 4, pattern_square_width)
        reverse = True # A switch for the angle 
        for size_1 in window(sizes): 
            for size_2 in window(sizes): 
                if reverse: 
                    display_single_pattern(size_1, size_2, hatches_2)
                else: 
                    display_single_pattern(size_1, size_2, hatches_1)
                reverse = not reverse
                
    # Display purple squares     
    for p in purple_patches: 
        ax.add_patch(p)

    total_figure_size = pattern_square_width * 3
    # Add a red cross in the center of the image 
    plt.scatter([total_figure_size / 2],[total_figure_size / 2],color='#a10000', marker="+",s=150, lw=2, zorder=1)
    
    # Clean extra whitespace around the plot and remove axes 
    axes = plt.gca()
    axes.set_xlim([0.,total_figure_size])
    axes.set_ylim([0.,total_figure_size])
    plt.axis('off')
    axes.xaxis.set_major_locator(NullLocator())
    axes.yaxis.set_major_locator(NullLocator())

    # convert matplotfig to bitmap and display it on bokeh figure
    bokehFig.image_rgba([np.flip(fig2data(fig),0)], x=[0], y=[0], dw=[1], dh=[1]) 

    #img = Image.fromarray(fig2data(fig), 'RGBA')
    #img.save('my.png')    

    plt.close(fig)
    return bokehFig
