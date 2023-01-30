import logging

from pdfminer.pdffont import PDFUnicodeNotDefined
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.utils import (bbox2str, mult_matrix,
                            translate_matrix,
                            matrix2str, apply_matrix_pt)
from pdfminer.layout import (LTTextLine, LTContainer, LTAnno,
                             LTText, LTComponent)
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


class LTComponentGeneric(LTComponent):
    """
    has a bbox and a polygon bound
    """
    def __init__(self, points):
        self.set_bound_points(points)

    def set_bound_points(self, points):
        self.pts = points
        self.polygon = Polygon(points)
        self.set_bbox(self.polygon.bounds)



class LTExpandableContainerGeneric(LTContainer, LTComponentGeneric):
    """
    with expandable bounds
    """

    def __init__(self) -> None:
        LTComponentGeneric.__init__(self, ())
        return

    def add(self, obj):
        LTContainer.add(self, obj)
        # TODO: fix this
        self.set_points(
            (
                min(self.x0, obj.x0),
                min(self.y0, obj.y0),
                max(self.x1, obj.x1),
                max(self.y1, obj.y1),
            )
        )


class LTTextLineGeneric(LTTextLine, LTExpandableContainerGeneric):
    """
    contains LTCharGenerics
    """

    def __init__(self, word_margin):
        LTTextLine.__init__(self, word_margin)
        self.word_margin = word_margin
        return

    def __repr__(self) -> str:
        return "<%s %s %r>" % (
            self.__class__.__name__,
            bbox2str(self.bbox),
            self.get_text(),
        )

    def analyze(self, laparams):
        #LTTextContainerGeneric.analyze(self, laparams)
        LTContainer.add(self, LTAnno("\n"))
        return


class LTCharGeneric(LTComponentGeneric, LTText):
    """
    char of any orientation
    """

    def __init__(self, matrix, font,
                 fontsize, scaling, rise,
                 text, textwidth, textdisp,
                 ncs, graphicstate):
        LTText.__init__(self)
        self._text = text
        self.matrix = matrix
        self.fontname = font.fontname
        self.ncs = ncs
        self.graphicstate = graphicstate
        self.adv = textwidth * fontsize * scaling
        # compute the boundary rectangle.
        if font.is_vertical():
            # vertical
            assert isinstance(textdisp, tuple)
            (vx, vy) = textdisp
            if vx is None:
                vx = fontsize * 0.5
            else:
                vx = vx * fontsize * 0.001
            vy = (1000 - vy) * fontsize * 0.001
            bbox_lower_left = (-vx, vy + rise + self.adv)
            bbox_upper_right = (-vx + fontsize, vy + rise)
        else:
            # horizontal
            descent = font.get_descent() * fontsize
            bbox_lower_left = (0, descent + rise)
            bbox_upper_right = (self.adv, descent + rise + fontsize)

        bbox_lower_right = (bbox_upper_right[0], bbox_lower_left[1])
        bbox_upper_left = (bbox_lower_left[0], bbox_upper_right[1])
        (a, b, c, d, e, f) = self.matrix
        #TODO: check this upright thing
        self.upright = 0 < a * d * scaling and b * c <= 0
        (x0, y0) = apply_matrix_pt(self.matrix, bbox_lower_left)
        (x1, y1) = apply_matrix_pt(self.matrix, bbox_lower_right)
        (x2, y2) = apply_matrix_pt(self.matrix, bbox_upper_right)
        (x3, y3) = apply_matrix_pt(self.matrix, bbox_upper_left)
        LTComponentGeneric.__init__(self, ((x0, y0),
                                           (x1, y1),
                                           (x2, y2),
                                           (x3, y3)))

        #TODO: should be done using the other bbox
        if font.is_vertical():
            self.size = self.width
        else:
            self.size = self.height
        return

    def get_text(self):
        return self._text

    # TODO: print the other bbox as well
    def __repr__(self) -> str:
        return "<%s %s matrix=%s font=%r adv=%s text=%r>" % (
            self.__class__.__name__,
            bbox2str(self.bbox),
            matrix2str(self.matrix),
            self.fontname,
            self.adv,
            self.get_text(),
        )


def forward_pos(point, delta, font, h_scaling):
    (x, y) = point
    if font.is_vertical():
        # horizontal scaling doesn't apply to vertical font position moves
        # but delta was already scaled using h_scaling.. so undo the scaling
        y += (delta/h_scaling)
    else:
        x += delta
    return (x, y)


class PDFGenericTextDevice(PDFTextDevice):

    def begin_textgroup(self):
        self._stack.append(self.cur_item)
        #TODO: the 0.1 should be parameterized
        self.cur_item = LTTextLineGeneric(0.1)


    def end_textgroup(self):
        tlg = self.cur_item
        assert isinstance(self.cur_item, LTTextLineGeneric), str(type(self.cur_item))
        self.cur_item = self._stack.pop()
        self.cur_item.add(tlg)


    def render_char_generic(self, matrix,
                            font, fontsize,
                            scaling, rise,
                            cid, ncs,
                            graphicstate):
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, str), str(type(text))
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTCharGeneric(
            matrix,
            font,
            fontsize,
            scaling,
            rise,
            text,
            textwidth,
            textdisp,
            ncs,
            graphicstate,
        )
        self.cur_item.add(item)
        return item.adv


    def render_string(self, textstate, seq, ncs, graphicstate):
        assert self.ctm is not None
        matrix = mult_matrix(textstate.matrix, self.ctm)
        font = textstate.font
        fontsize = textstate.fontsize
        scaling = textstate.scaling * 0.01
        charspace = textstate.charspace * scaling
        wordspace = textstate.wordspace * scaling
        #TODO: check if font size needs to be applied to rise, charspace and wordspace
        rise = textstate.rise
        assert font is not None
        if font.is_multibyte():
            wordspace = 0
        dxscale = 0.001 * fontsize * scaling
        (x, y) = textstate.linematrix
        needcharspace = False
        for obj in seq:
            if isinstance(obj, (int, float)):
                x, y = forward_pos((x, y), -(obj * dxscale), font, scaling)
                needcharspace = True
            else:
                for cid in font.decode(obj):
                    if needcharspace:
                        x, y = forward_pos((x, y), charspace, font, scaling)
                    adv = self.render_char_generic(
                        translate_matrix(matrix, (x, y)),
                        font,
                        fontsize,
                        scaling,
                        rise,
                        cid,
                        ncs,
                        graphicstate,
                    )
                    x, y = forward_pos((x, y), adv, font, scaling)
                    if cid == 32 and wordspace:
                        x, y = forward_pos((x, y), wordspace, font, scaling)
                    needcharspace = True
        textstate.linematrix = (x, y)



class PDFPageGenericTextAggregator(PDFPageAggregator,
                                   PDFGenericTextDevice):
    pass



class PDFPageGenericTextInterpreter(PDFPageInterpreter):
    def __init__(self, rsrcmgr, device):
        assert isinstance(device, PDFGenericTextDevice), str(type(device))
        PDFPageInterpreter.__init__(self, rsrcmgr, device)

    def do_BT(self):
        PDFPageInterpreter.do_BT(self)
        self.device.begin_textgroup()

    def do_ET(self):
        PDFPageInterpreter.do_ET(self)
        self.device.end_textgroup()


