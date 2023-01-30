import sys
import logging
from geospatial_pdf.layers.high_level import parse_layered_pdf_file
#from geospatial_pdf.generictext.high_level import parse_generic_text_pdf_file
from geospatial_pdf.geospatial.high_level import parse_geospatial_pdf_file
from geospatial_pdf.debug_utils import print_layout


def print_simple(pinfo):
    for info in pinfo:
        print_layout(info)

def print_layered(pinfo):
    for k, layers in pinfo.items():
        print(f'pageno: {k}')
        for layer, linfo in layers.items():
            print(f'layer: {layer}')
            print_layout(linfo)

filename = sys.argv[1]
logging.basicConfig(level=logging.INFO)
logging.getLogger('pdfminer').setLevel(logging.WARNING)
#pinfo = parse_generic_text_pdf_file(filename)
#print_simple(pinfo)
pinfo = parse_layered_pdf_file(filename)
#pinfo = parse_geospatial_pdf_file(filename)
print_layered(pinfo)

