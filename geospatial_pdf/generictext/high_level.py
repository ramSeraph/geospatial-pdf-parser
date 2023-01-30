from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from . import (PDFPageGenericTextAggregator,
               PDFPageGenericTextInterpreter)


def parse_generic_text_pdf_file(filename):
    with open(filename, "rb") as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed(
                f"Text extraction is not allowed: {filename}"
            )
 
        rsrcmgr = PDFResourceManager(caching=True)
        device = PDFPageGenericTextAggregator(rsrcmgr)
        interpreter = PDFPageGenericTextInterpreter(rsrcmgr, device)
        pno = 0
        pinfo = []
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            page_layout = device.get_result()
            pinfo.append(page_layout)
            pno += 1
    return pinfo
