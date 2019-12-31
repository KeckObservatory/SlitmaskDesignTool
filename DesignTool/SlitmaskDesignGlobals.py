
from smdtLogger import SMDTLogger
from SlitmaskDesignTool import SlitmaskDesignTool


GlobalData = {}

def _getData(_id):
    d = GlobalData.get(_id)
    if not d:
        d = SlitmaskDesignTool(b'', 0, None)
    return d


def _setData(_id, smdata):
    GlobalData[_id] = smdata


class SMDesign():
    PNGImage = "image/png"

    def __init__(self):
        self.sm = _getData('smdt')
        self.config = None

    def log_message(self, msg, **args):
        SMDTLogger.info(msg, *args)

smd = SMDesign()
