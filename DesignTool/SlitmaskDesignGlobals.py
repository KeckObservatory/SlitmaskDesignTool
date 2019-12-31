
from smdtLogger import SMDTLogger
from SlitmaskDesignTool import SlitmaskDesignTool


GlobalData = {}


def _get_data(_id):
    d = GlobalData.get(_id)
    if not d:
        d = SlitmaskDesignTool(b'', 0, None)
    return d


def _set_data(_id, smdata):
    GlobalData[_id] = smdata


class SMDesign:
    PNGImage = "image/png"

    def __init__(self):
        self.sm = _get_data('smdt')
        self.config = None

    def log_message(self, msg, **args):
        SMDTLogger.info(msg, *args)


smd = SMDesign()
