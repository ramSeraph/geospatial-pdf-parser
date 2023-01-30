from . import (PDFPageOptionalGenericTextAggregator,
               PDFOptionalGenericTextInterpreter)

from ..layers.high_level import parse_layered_pdf_file

def parse_geospatial_pdf_file(filename,
                              laparams=None):

    return parse_layered_pdf_file(filename,
                                  AggregatorClass=PDFPageOptionalGenericTextAggregator,
                                  InterpreterClass=PDFOptionalGenericTextInterpreter,
                                  laparams=laparams)
