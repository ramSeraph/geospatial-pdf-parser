import shutil
import tempfile
import logging

from pathlib import Path

import ghostscript

from imgcat import imgcat
from PIL import (
    Image,
    ImageDraw,
    ImageColor
)
from pdfminer.layout import (
    LTTextLineHorizontal,
    LTTextLineVertical,
    LTImage
)

logger = logging.getLogger(__name__)

# https://stackoverflow.com/a/22726782
class TemporaryDirectory(object):
    def __init__(self, auto_delete=True):
        self.auto_delete = auto_delete
        self.name = None

    def remove(self):
        if self.name is not None:
            shutil.rmtree(self.name)

    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.auto_delete:
            self.remove()


def get_png_path(pno, filename, tempdir):
    png_path = str(Path(tempdir).joinpath(filename)).replace('.pdf', f'.{pno}.png')
    if Path(png_path).exists():
        return png_path

    resolution = 300
    logger.info(f'creating temp file at {png_path}')
    Path(png_path).parent.mkdir(exist_ok=True, parents=True)
    gs_command = [
        "gs",
        "-q",
        "-sDEVICE=png16m",
        f"-sPageList={pno+1}",
        "-o",
        png_path,
        f"-r{resolution}",
        filename,
    ]
    ghostscript.Ghostscript(*gs_command)
    return png_path



def get_show_params(pno, filename, tempdir, layout,  show_original=False):

    png_path = get_png_path(pno, filename, tempdir)
    img = Image.open(png_path)
    if show_original:
        imgcat(img)

    pdf_width, pdf_height = layout.bbox[2], layout.bbox[3]
    img_width, img_height = img.size
    img_width_scaler = img_width / float(pdf_width)
    img_height_scaler = img_height / float(pdf_height)
    img_scaler = (img_width_scaler, img_height_scaler, img_height)

    # draw ruler
    #draw = ImageDraw.Draw(img)
    #draw.line((0,0), (img_width, 0), fill=getrgb('black'), width=2)
    #draw.line((0,0), (0, img_height), fill=getrgb('black'), width=2)
    #num_x_slots = math.floor(pdf_width/50)
    #num_y_slots = math.floor(pdf_height/50)
    

    return img, img_scaler


def scale_bbox(bbox, scalers):
    (x0, y0, x1, y1) = bbox
    x_scale, y_scale, height = scalers
    sx0 = x0*x_scale
    sy0 = y0*y_scale
    sx1 = x1*x_scale
    sy1 = y1*y_scale
    return sx0, abs(sy0 - height), sx1, abs(sy1 - height) 


def show_objs(pno, filename, tempdir, layout, objs, color, show_original=False):

    img, img_scaler = get_show_params(pno, filename, tempdir, layout, show_original=show_original)

    draw = ImageDraw.Draw(img)
    item_bboxes = [ i.bbox for i in objs ]
    scaled_bboxes = [ scale_bbox(b, img_scaler) for b in item_bboxes ]
    for bbox in scaled_bboxes:
        draw.rectangle(bbox, outline=ImageColor.getrgb(color), fill=None, width=5)
    imgcat(img)



def print_img(layout):
    pass


def print_layout(layout, img_print=False, indent=0):
    indent_str = '  '*indent
    logger.info(f'{indent_str}{layout}')
    if isinstance(layout, LTTextLineHorizontal) or isinstance(layout, LTTextLineVertical):
        return

    if isinstance(layout, LTImage):
        if img_print:
            print_img(layout)

    objs = getattr(layout, '_objs', [])
    for obj in objs:
        print_layout(obj, img_print=img_print, indent=indent+1)


