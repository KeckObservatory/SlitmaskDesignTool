import sys


class ConfigFile:

    def __init__(self, fileName):
        self.fileName = fileName
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
        with open(fname, 'r') as fh:
            props = {}
            for line in fh:
                parts = line.strip().split('=')
                if len(parts) > 1:
                    key, val = parts
                    key = key.strip()
                    val = val.strip().replace('"', '').replace("'", "")
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
