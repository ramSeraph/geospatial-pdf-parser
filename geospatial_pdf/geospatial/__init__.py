import logging
from ..layers import PDFPageOptionalAggregator, PDFPageOptionalInterpreter
from ..generictext import PDFGenericTextDevice, PDFPageGenericTextInterpreter

logger = logging.getLogger(__name__)

class PDFPageOptionalGenericTextAggregator(PDFPageOptionalAggregator,
                                           PDFGenericTextDevice):

    def begin_textgroup(self):
        PDFGenericTextDevice.begin_textgroup(self)
        for i, active in enumerate(self.active_status):
            if not active:
                return
            logger.info(f'executing begin textgroup for layer {self.active_combo_lists[i]}')
            with self.layer_context(i):
                PDFGenericTextDevice.begin_textgroup(self)

    def end_textgroup(self):
        PDFGenericTextDevice.end_textgroup(self)
        for i, active in enumerate(self.active_status):
            if not active:
                return
            logger.info(f'executing end textgroup for layer {self.active_combo_lists[i]}')
            with self.layer_context(i):
                PDFGenericTextDevice.end_textgroup(self)


class PDFOptionalGenericTextInterpreter(PDFPageOptionalInterpreter,
                                        PDFPageGenericTextInterpreter):
    pass
