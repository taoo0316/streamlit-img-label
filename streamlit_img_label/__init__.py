import os
import streamlit.components.v1 as components
from PIL import Image
import numpy as np

_RELEASE = False

if not _RELEASE:
    _component_func = components.declare_component(
        "st_img_label",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_img_label", path=build_dir)


def _resize_img(img: Image, max_height: int=700, max_width: int=700):
    """
    Resize the image to be a max of 700x700 by default, or whatever the user 
    provides. If streamlit has an attribute to expose the default width of a widget,
    we should use that instead.
    """
    if img.height > max_height:
        ratio = max_height / img.height
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))
    if img.width > max_width:     
        ratio = max_width / img.width
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))
    return img

def _recommended_box(img: Image):
    # Find a recommended box for the image (could be replaced with image detection)
    box = (img.width * 0.2, img.height * 0.2, img.width * 0.8, img.height * 0.8)
    box = [int(i) for i in box]
    height = box[3] - box[1]
    width = box[2] - box[0]

    left, top = box[0], box[1]
    return {'left' : int(left), 'top' : int(top), 'width' : int(width), 'height' : int(height)}


def st_img_label(img: Image, box_color: str='blue',
               return_type: str='image', box_algorithm=None,  key=None):
    """Create a new instance of "st_img_label".

    Parameters
    ----------
    img_file: PIL.Image
        The image to be croppepd
    box_color: string
        The color of the cropper's bounding box. Defaults to blue, can accept 
        other string colors recognized by fabric.js or hex colors in a format like
        '#ff003c'
    aspect_ratio: tuple
        Tuple representing the ideal aspect ratio: e.g. 1:1 aspect is (1,1) and 4:3 is (4,3)
    box_algorithm: function
        A function that can return a bounding box, the function should accept a PIL image
        and return a dictionary with keys: 'left', 'top', 'width', 'height'. Note that
        if you use a box_algorithm with an aspect_ratio, you will need to decide how to
        handle the aspect_ratio yourself
    return_type: str
        The return type that you would like. The default, 'image', returns the cropped
        image, while 'box' returns a dictionary identifying the box by its
        left and top coordinates as well as its width and height.
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.

    Returns
    -------
    PIL.Image
    The cropped image in PIL.Image format
    """

    # Ensure that the return type is in the list of supported return types
    supported_types = ('image', 'box')
    if return_type.lower() not in supported_types:
        raise ValueError(f"{return_type} is not a supported value for return_type, try one of {supported_types}")
    # Load the image and resize to be no wider than the streamlit widget size 
    img = _resize_img(img)

    # Find a default box
    if not box_algorithm:
        box = _recommended_box(img)
    else:
        box = box_algorithm(img)
    rectLeft = box['left']
    rectTop = box['top']
    rectWidth = box['width']
    rectHeight = box['height']

    # Get arguments to send to frontend
    canvasWidth = img.width
    canvasHeight = img.height
    lockAspect = False

    # Translates image to a list for passing to Javascript
    imageData = np.array(img.convert("RGBA")).flatten().tolist()

    # Call through to our private component function. Arguments we pass here
    # will be sent to the frontend, where they'll be available in an "args"
    # dictionary.
    #
    # Defaults to a box whose vertices are at 20% and 80% of height and width. 
    # The _recommended_box function could be replaced with some kind of image
    # detection algorith if it suits your needs.
    component_value = _component_func(canvasWidth=canvasWidth, canvasHeight=canvasHeight,
                                      rectHeight=rectHeight, rectWidth=rectWidth, rectLeft=rectLeft, rectTop=rectTop,
                                      boxColor=box_color, imageData=imageData, lockAspect=not(lockAspect), key=key)

    # Return a cropped image using the box from the frontend
    if component_value:
        rect = component_value['coords']
    else:
        rect = box

    # Return the value desired by the return_type
    if return_type.lower() == 'image':
        cropped_img = img.crop((rect['left'], rect['top'], rect['width'] + rect['left'], rect['height'] + rect['top']))
        return cropped_img
    elif return_type.lower() == 'box':
        return rect


# Add some test code to play with the component while it's in development.
# During development, we can run this just as we would any other Streamlit
# app: `$ streamlit run my_component/__init__.py`
if not _RELEASE:
    import streamlit as st
    st.set_option('deprecation.showfileUploaderEncoding', False)
    # Upload an image and set some options for demo purposes
    img_file = st.sidebar.file_uploader(label='Upload a file', type=['png', 'jpg'])

    if img_file:
        img = Image.open(img_file)
        # Get a cropped image from the frontend
        cropped_img = st_img_label(img, box_color='#0000FF')
        
        # Manipulate cropped image at will
        st.write("Preview")
        _ = cropped_img.thumbnail((150,150))
        st.image(cropped_img)

    
