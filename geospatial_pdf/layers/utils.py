import logging

from pdfminer.psparser import LIT
from pdfminer.pdftypes import resolve_all
from pdfminer.utils import decode_text

logger = logging.getLogger(__name__)

LITERAL_OCG = LIT('OCG')
LITERAL_OCMD = LIT('OCMD')

# utf-16le is not a valid pdf text encoding, but it was used by ESRI folks
def decode_text_special(s):
    if s.startswith(b"\xff\xfe"):
        return str(s[2:], "utf-16le", "ignore")
    return decode_text(s)


def get_OCG_info_from_doc(doc):
    OCPs = doc.catalog.get('OCProperties', None)
    if OCPs is None:
        return None, None

    OCPs = resolve_all(OCPs)
    OCGs = OCPs.get('OCGs', None)

    if OCGs is None:
        return None, None

    OCG_names = []
    for OCG in OCGs:
        #typ = OCG['Type']
        #if typ != KEYWORD_OCG:
        #    raise Exception(f'Unexpected type in OCG listing: {typ}')
        OCG_name_raw = OCG['Name']
        name = decode_text_special(OCG_name_raw)
        OCG_names.append(name)

    default = OCPs.get('D', None)
    if default is None:
        return OCG_names, None
    order_list = default.get('Order', None)
    if order_list is None:
        return OCG_names, None
    return OCG_names, order_list


def get_order_map_from_list(order_list):
    order_map = {}
    prev_key = None
    for item in order_list:
        if type(item) == list:
            if prev_key is None:
                raise Exception('non list element expected before list element')
            sub_map = get_order_map_from_list(item)
            order_map[prev_key] = sub_map
            prev_key = None
        else:
            name = decode_text_special(item['Name'])
            order_map[name] = {}
            prev_key = name
    return order_map


def _get_active_combos_int(order_map, full_list, path):
    path_new = path.copy() 
    if len(order_map) == 0:
        full_list.append(path_new)
    for l_name, val in order_map.items():
        _get_active_combos_int(val, full_list, path_new + [l_name])


def get_active_combos(order_map):
    full_list = []
    _get_active_combos_int(order_map, full_list, [])
    return full_list
 

def get_page_OC_map(page):
    properties = resolve_all(page.resources['Properties'])
    known_OCs = {}
    layer_name_to_OCs = {}
    for prop_name, prop_value in properties.items():
        prop_type = prop_value['Type']
        if prop_type not in [ LITERAL_OCG, LITERAL_OCMD ]:
            continue
        layer_name = decode_text_special(prop_value['Name'])
        known_OCs[prop_name] = layer_name
        layer_name_to_OCs[layer_name] = prop_name
    return layer_name_to_OCs
 
