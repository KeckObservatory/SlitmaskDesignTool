import sys
import json

class ConfigFile:

    def __init__(self, fileName, split=False):
        self.fileName = fileName
        self.split = split
        self.properties = {}
        self.readConfigFile(fileName)

    def getType (self, value):
        try:
            i = int(value)
            return i
        except:
            try:
                f = float(value)
                return f
            except:
                if value == "True":
                    return True
                if value == "False":
                    return False
                return value

    def readConfigFile (self, fname):
        def clean(s):
            return s.strip().replace('"', '').replace("'", "")
        
        with open(fname, 'r') as fh:
            props = {}
            for line in fh:
                parts = line.strip().split('=')
                if len(parts) > 1:
                    key, val = parts
                    key = key.strip()
                    if self.split:
                        val = [clean(s) for s in val.split(',')]
                    else:
                        val = clean(val)                    
                    props[key] = self.getType (val)
            self.properties = props
            return
        raise Exception("Failed to read configuration file " + fname)

    def get(self, key, defValue=''):
        if key in self.properties:
            return self.properties[key]
        else:
            return defValue

if __name__ == "__main__":
    ccf = ConfigFile (sys.argv[1])
    for k, v in ccf.properties.items():
        print (k, v)
