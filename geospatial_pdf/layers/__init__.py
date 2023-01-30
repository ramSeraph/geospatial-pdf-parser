import logging

from pdfminer.psparser import LIT
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage


logger = logging.getLogger(__name__)

# N.B.
# only implements a minor part of the Optional Content specs..
#
# OCG to OCMD mapping is not handled
#   - should be easy enough to add.. might need to move from name based system to an id based system?
#   - Need a sample file to work with
# OC specifications in XObject and Annotations are not handled
#   - should also be easy to add.. I don't have sample file which uses this
# Intent and Usage Application Dictionaries I didn't even touch..
#   - though this feels more like a display related problem
# Some other complicated stuff I am ignoring
#  - From the pdf spec : 
#    Sections of content in a content stream (including a page's Contents stream, a
#    form or pattern’s content stream, glyph descriptions a Type 3 font as specified by
#    its CharProcs entry, or an annotation’s appearance) can be made optional by enclosing them between the marked-content operators BDC and EMC 
#  - Not masochistic enough to attempt this

# TODO: don't know enough about python typehints to make them work


LITERAL_OC = LIT('OC')


# According to the PDF Spec, all painting operations and their graphic side effects
# need to be there even if the layer is switched off.. 
# so we let PDFPageAggregator go through the motions of curve drawing and text writing
# and then remove the added LTChars/LTImages and other elements from the final list
# depending on whether we are active or not
class PDFPageOptionalAggregator(PDFPageAggregator):

    def __init__(self,
                 rsrcmgr,
                 pageno=1,
                 laparams=None,
                 handle_textgroup=False):
        if handle_textgroup:
            if laparams is not None:
                logger.warning('handle_textgroup is set to True' + \
                               ' and laparams is not None.. ignoring laparams')
            laparams = None

        PDFPageAggregator.__init__(self, rsrcmgr,
                                   pageno=pageno,
                                   laparams=laparams)
        self.OC_stack = []
        self.set_active_combo_lists([])
        self.handle_textgroup = handle_textgroup


    def layer_context(self, i):
        outer = self
        class Ctx:
            def __init__(self, i):
                self.i = i
                self.outer = outer
                self.old_stack = None
                self.old_cur = None

            def __enter__(self):
                self.old_stack = self.outer._stack
                self.old_cur = self.outer.cur_item
                self.outer.cur_item = self.outer.layers[self.i]
                self.outer._stack = self.outer.layer_stacks[self.i]
                return self

            def __exit__(self, type, value, traceback):
                self.outer.layers[i] = self.outer.cur_item
                self.outer.layer_stacks[i] = self.outer._stack
                self.outer.cur_item = self.old_cur
                self.outer._stack = self.old_stack

        return Ctx(i)
        

    def get_status(self, combo_list):
        if combo_list is None:
            return True

        active = True
        for OC_name in self.OC_stack:
            if OC_name is None:
                continue
            if OC_name not in combo_list:
                active = False
                break
        return active


    def set_active_status(self):
        self.active_status = [ self.get_status(combo_list) for combo_list in self.active_combo_lists ] 


    def set_active_combo_lists(self, combo_lists):
        self.active_combo_lists = combo_lists
        self.set_active_status()


    def activate_OC(self, OC_name):
        self.OC_stack.append(OC_name)
        self.set_active_status()
        logger.debug(f'current stack: {self.OC_stack}')


    def deactivate_last_OC(self):
        self.OC_stack.pop()
        self.set_active_status()
        logger.debug(f'current stack: {self.OC_stack}')


    def add_last_to_layers(self):
        #TODO: using [-1] to access last element is a hack
        # it is not part of the pdfminer LTContainer interface
        ltobj = self.cur_item._objs[-1]
        for i, active in enumerate(self.active_status):
            if not active:
                continue
            self.layers[i].add(ltobj)


    def receive_layout(self, ltpage):
        self.result.append(ltpage)


    def begin_page(self, page, ctm):
        PDFPageAggregator.begin_page(self, page, ctm)
        ltpage = self.cur_item
        num_combos = len(self.active_combo_lists)
        self.layers = [
            LTPage(ltpage.pageid, ltpage.bbox, rotate=ltpage.rotate)
            for _ in range(num_combos)
        ]
        self.layer_stacks = [
            []
            for _ in range(num_combos)
        ]
        self.result = []


    def end_page(self, page):
        PDFPageAggregator.end_page(self, page)
        self.pageno -= 1
        num_layers = len(self.layers)
        for i in range(num_layers):
            with self.layer_context(i):
                PDFPageAggregator.end_page(self, page)
            self.pageno -= 1
        self.pageno += 1


    def begin_figure(self, name, bbox, matrix):
        PDFPageAggregator.begin_figure(self, name, bbox, matrix)
        for i, active in enumerate(self.active_status):
            if not active:
                return
            logger.debug(f'executing begin figure for layer {self.active_combo_lists[i]}')
            with self.layer_context(i):
                PDFPageAggregator.begin_figure(self, name, bbox, matrix)


    def end_figure(self, _):
        PDFPageAggregator.end_figure(self, _)
        for i, active in enumerate(self.active_status):
            if not active:
                return
            logger.debug(f'executing end figure for layer {self.active_combo_lists[i]}')
            with self.layer_context(i):
                PDFPageAggregator.end_figure(self, _)


    def render_image(self, name, stream):
        PDFPageAggregator.render_image(self, name, stream)
        self.add_last_to_layers()


    def paint_path(self, gstate, stroke, fill, evenodd, path):
        count_before = len(self.cur_item._objs)
        PDFPageAggregator.paint_path(self, gstate, stroke, fill, evenodd, path)
        count_after = len(self.cur_item._objs)

        # deal with the fact that paint_path can be called recursively
        if count_after - count_before == 1:
            self.add_last_to_layers()


    def render_char(self, matrix, font,
                    fontsize, scaling, rise,
                    cid, ncs, graphicstate):
        adv = PDFPageAggregator.render_char(self, matrix, font,
                                            fontsize, scaling, rise,
                                            cid, ncs, graphicstate)
        self.add_last_to_layers()
        return adv


class PDFPageOptionalInterpreter(PDFPageInterpreter):

    def __init__(self, rsrcmgr, device):
        assert isinstance(device, PDFPageOptionalAggregator), str(type(device))
        PDFPageInterpreter.__init__(self, rsrcmgr, device)


    def do_BDC(self, tag, props):
        OC_name = props.name if tag == LITERAL_OC else None
        logger.info(f'activating OC {OC_name}')
        self.device.activate_OC(OC_name)
        return PDFPageInterpreter.do_BDC(self, tag, props)


    def do_EMC(self):
        logger.info('deactivating last OC')
        self.device.deactivate_last_OC()
        return PDFPageInterpreter.do_EMC(self)


