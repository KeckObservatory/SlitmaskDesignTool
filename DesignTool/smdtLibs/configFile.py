import sys
import json
import os
from configparser import ConfigParser
import pkg_resources


class ConfigFile(ConfigParser):
    def __init__(self, fileName, **kwargs):
        """
        Format of config file is keyword = value, one per line
        split=True if, fields are comma separated values; False, if single value.
        """
        super(ConfigFile, self).__init__(kwargs)
        self.fileName = fileName
        self.default_secion = kwargs.get("default_section", "DEFAULT")
        self.properties = {}
        if fileName is not None:
            self.read(fileName)

    def _getType(self, value):
        if not isinstance(value, str):
            return value

        value = value.strip()

        valueIC = value.lower()
        if valueIC == "true":
            return True
        if valueIC == "false":
            return False
        if valueIC == "none":
            return None

        try:
            return eval(value)
        except Exception:
            pass

        try:
            i = int(value)
            return i
        except:
            pass

        try:
            f = float(value)
            return f
        except:
            pass

        return value

    def _getPath(self, path):
        """
        If path is regular path then returns it.
        Else tries to find it in the resources, ie where the source code is.
        """
        if path is None:
            return None

        if os.path.isfile(path):
            return path
        else:
            fullpath = pkg_resources.resource_filename(__name__, path)
            if os.path.isfile(fullpath):
                return fullpath

        return None

    def read(self, cgfile):
        """
        Reads config using super class reader.
        Then digests the content, ie. gets the right types for the values.
        """

        def digestItems(sec, known):
            values = self.items(sec)
            secValues = {}
            for k, v in values:
                if k in known:
                    continue
                secValues[k] = self._getType(v)
            return secValues

        path = self._getPath(cgfile)
        if path is None:
            raise Exception(f"Config file {cgfile} not found")
        super().read(path)

        self.properties.update(digestItems(self.default_section, {}))
        sections = self.sections()

        for sec in sections:
            self.properties[sec] = digestItems(sec, self.properties)

    def __getattr__(self, key):
        val = self.properties.get(key.lower())
        if val is not None:
            return val

        if key in self.sections():
            return dict(self.items(key))

        return None

    def getValue(self, key, defValue=None):
        if key is None:
            return defValue
        val = self.properties.get(key.lower())
        if val is None:
            return defValue
        return val

    def setValue(self, key, value):
        self.properties[key] = value
