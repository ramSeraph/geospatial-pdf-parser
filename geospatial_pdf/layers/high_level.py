import logging

from pprint import pformat

from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.layout import LAParams


from . import (PDFPageOptionalAggregator,
               PDFPageOptionalInterpreter)

from .utils import (
    get_OCG_info_from_doc,
    get_active_combos,
    get_page_OC_map,
    get_order_map_from_list
)

logger = logging.getLogger(__name__)

# TODO: take order list as a function argument?
def parse_layered_pdf_file(filename,
                           AggregatorClass=PDFPageOptionalAggregator,
                           InterpreterClass=PDFPageOptionalInterpreter,
                           laparams=None):
    with open(filename, "rb") as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed(
                f"Text extraction is not allowed: {filename}"
            )
        OCGs, order_list = get_OCG_info_from_doc(document)
        if OCGs is None:
            raise Exception('file does not have OCGs')
    
        if order_list is None:
            raise Exception('file does not have an order map')
    
        order_map = get_order_map_from_list(order_list)
        logger.info(f'order map:\n{pformat(order_map)}')
        combo_list = get_active_combos(order_map)
        logger.info(f'order list:\n{pformat(combo_list)}')

        rsrcmgr = PDFResourceManager(caching=True)
        device = AggregatorClass(rsrcmgr, laparams=laparams)
        interpreter = InterpreterClass(rsrcmgr, device)
    
        page_info = {}
        pno = 0
        for page in PDFPage.create_pages(document):
            layer_name_to_OCs = get_page_OC_map(page)
            OC_combos = [
                [ layer_name_to_OCs[x] for x in l ]
                for l in combo_list
            ]
            logger.info(f'order list OCs:\n{pformat(OC_combos)}')
            device.set_active_combo_lists(OC_combos)
            interpreter.process_page(page)
            page_layouts = device.get_result()
            full_page_layout = page_layouts[0]
            page_layouts = page_layouts[1:]
    
            page_info[pno] = {}
            for i, OC_combo in enumerate(OC_combos):
                layer_names = ', '.join(combo_list[i])
                logger.info(f'showing layout with only {OC_combo} {layer_names} switched on')
                layout = page_layouts[i]
                #print_layout(layout)
                #show_objs(pno, filename, tempdir, layout, layout, 'red', show_original=False)
                page_info[pno][layer_names] = layout
            page_info[pno][''] = full_page_layout
        pno += 1
    return page_info


