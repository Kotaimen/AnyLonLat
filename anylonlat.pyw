#!/usr/bin/env pythonw
# -*- encoding: utf-8 -*-



"""Convert between various LonLat formats"""

import re
import math
import webbrowser

# Support both Python 2.x and Python 3.x, and use ttk when possible 
import sys
if sys.hexversion >= 0x3010000:
    from tkinter import *
    if TkVersion >= 8.5:
        from tkinter.ttk import *
elif sys.hexversion >= 0x3000000:
    from tkinter import *
elif sys.hexversion >= 0x2070000:
    from Tkinter import *
    if TkVersion >= 8.5:
        from ttk import *
elif sys.hexversion >= 0x2050000:
    from Tkinter import *
else:
    raise ImportError('Requires Python 2.6 or higher')

__author__ = 'Kotaimen <kotaimen@pset.suntec.net>'
__copyright__ = 'Public Domain'
__version__ = '1.4'

# modified at 2010-12-23 by ZHANG Peng for a loose DMS syntax and Navi Application Display Favour

#===============================================================================
# Converter I/F
#===============================================================================

class LonLatConvertFailed(Exception):
    """Exception when LonLat conversion is failed"""
    pass


class LonLatConverter(object):
    """ Converter I/F
    The standard LonLat format is a tuple:
        (Longitude, Latitude)
    Both Longitude Latitude is a float number:
        Longitude > 0   W
        Longitude < 0   E
        Latitude > 0    N
        Latitude < 0    S
    
    """

    def getFormatName(self):
        """Get Name of the format"""
        return self._FORMAT_NAME

    def fromString(self, lonlat):
        """Convert a string to standard LonLat, raise ConvertFailed when
        format Mismatch"""
        raise NotImplemented

    def toString(self, lonlat):
        """Convert a standard LonLat to a string"""
        raise NotImplemented

#===============================================================================
# Degrees Related Converters
#===============================================================================

class DDDConverter(LonLatConverter):

    """Default Decimal Degrees"""

    _FORMAT_NAME = 'Decimal Degrees (DDD)'

    _PATTERN_FROM_STRING = re.compile(# look for a float number pair
        r'^(?P<lon>[-+]?\d+\.\d*)[, ]+(?P<lat>[-+]?\d+\.\d*)$')

    def fromString(self, lonlat):
        match = self._PATTERN_FROM_STRING.match(lonlat)
        if not match:
            raise LonLatConvertFailed()

        lonstr = match.group('lon')
        latstr = match.group('lat')

        return self._lonstr2lon(lonstr), self._latstr2lat(latstr)

    def _lonstr2lon(self, lonstr):
        return float(lonstr)

    def _latstr2lat(self, latstr):
        return float(latstr)

    def toString(self, lonlat):
        return '%.7f, %.7f' % (lonlat)


class WolframAlphaConverter(DDDConverter):

    """DDD in WolframAlpha Favour"""

    _FORMAT_NAME = 'DDD (WolframAlpha Favour)'

    _PATTERN_FROM_STRING = re.compile(
        r'^(?P<lon>\d+\.\d*[WE]) (?P<lat>\d+\.\d*[NS])$')

    def _lonstr2lon(self, lonstr):
        if lonstr[-1:] == 'E': # end with 'E'
            return float(lonstr[:-1])
        else:
            return - float(lonstr[:-1])

    def _latstr2lat(self, latstr):
        if latstr[-1:] == 'N': # end with 'N'
            return float(latstr[:-1])
        else:
            return - float(latstr[:-1])

    def toString(self, lonlat):
        lon, lat = lonlat
        lonstr = '%.8f%s' % (math.fabs(lon), 'E' if lon >= 0 else 'W')
        latstr = '%.8f%s' % (math.fabs(lat), 'N' if lat >= 0 else 'S')
        return '%s %s' % (lonstr, latstr)


class HexConverter(DDDConverter):

    """DDD in 1/256 Degree used by Navi/WMV"""

    _FORMAT_NAME = 'Hexadecimal 1/256 Degrees (WMV Favour)'

    _PATTERN_FROM_STRING = re.compile(# look for hex pair"
        r'^(?P<lon>[0-9a-f]+),\s*(?P<lat>[0-9a-f]+)$', re.I)

    _FACTOR = 1. * 60 * 60 * 256

    def toString(self, lonlat):
        return '%x, %x' % (self._cvt2(lonlat[0]), self._cvt2(lonlat[1]))

    def _lonstr2lon(self, lonstr):
        return self._cvt1(lonstr, 0x9e34000) #180deg

    def _latstr2lat(self, latstr):
        return self._cvt1(latstr, 0x4f1a000) #90deg

    def _cvt1(self, s, limit):
        x = int(s, 16)
        if x <= limit:
            return x / self._FACTOR
        else:
            return (x - 2 ** 32) / self._FACTOR

    def _cvt2(self, x):
        y = math.trunc(x * self._FACTOR)
        if y >= 0:
            return y
        else:
            return 2 ** 32 + y


class HexConverterC(HexConverter):

    _FORMAT_NAME = 'Hexadecimal (C Favour)'

    _PATTERN_FROM_STRING = re.compile(r'^0x(?P<lon>[0-9a-f]+),\s*0X(?P<lat>[0-9a-f]+)$', re.I)

    def toString(self, lonlat):
        result = HexConverter.toString(self, lonlat)
        return '0x%s, 0x%s' % tuple(map(lambda s: s.strip(), result.split(',')))


class DecConverter(DDDConverter):

    """1/256 Degree used by L-FormatViewer"""

    _FORMAT_NAME = '1/256 Degree used by L-FormatViewer JP'

    _PATTERN_FROM_STRING = re.compile(# look for hex pair"
        r'^D (?P<lon>-?\d+),\s*(?P<lat>-?\d+)$', re.I)

    _FACTOR = 1. * 60 * 60 * 256

    def toString(self, lonlat):
        return 'D %d, %d' % (self._cvt2(lonlat[0]), self._cvt2(lonlat[1]))

    def _lonstr2lon(self, lonstr):
        return self._cvt1(lonstr, 0x9e34000) #180deg

    def _latstr2lat(self, latstr):
        return self._cvt1(latstr, 0x4f1a000) #90deg

    def _cvt1(self, s, limit):
        x = int(s)
        if x <= limit:
            return x / self._FACTOR
        else:
            return (x - 2 ** 32) / self._FACTOR

    def _cvt2(self, x):
        y = math.trunc(x * self._FACTOR + 0.5)
        if y >= 0:
            return y
        else:
            return 2 ** 32 + y

class PIDConverter(HexConverter):

    """Hexadecimal Parcel ID used by WMV"""

    _FORMAT_NAME = 'Parcel ID (WMV Favour)'

    _IDENTIFY_EWSN_MASK = 0x80000000 # Mask for identifying East/West/South/North

    _IDENTIFY_EXTENDED_AREA_MASK = 0xff # Mask for identifying extended area

    _IGNORE_EXTRA_BIT_SHIFT = 3

    _PATTERN_FROM_STRING = re.compile(
        r'\s*PID\s+(0x)?(?P<lon>[0-9a-f]+)\s*,\s*(0x)?(?P<lat>[0-9a-f]+)$', re.I)

    def toString(self, lonlat):
        lon = lonlat[0]
        lat = lonlat[1]

        # longitude
        if lon < 0: # longitude west
            lon_msk = self._IDENTIFY_EWSN_MASK
        else:       # longitude east
            lon_msk = 0

        # approximate convert
        plon = math.trunc(abs(lon) * self._FACTOR + 0.5)
        plon &= ~self._IDENTIFY_EXTENDED_AREA_MASK
        plon <<= self._IGNORE_EXTRA_BIT_SHIFT
        plon |= lon_msk

        # latitude
        if lat < 0: # latitude south
            lat_msk = self._IDENTIFY_EWSN_MASK
        else:
            lat_msk = 0

        # approximate convert
        plat = math.trunc(abs(lat) * self._FACTOR + 0.5)
        plat &= ~self._IDENTIFY_EXTENDED_AREA_MASK
        plat <<= self._IGNORE_EXTRA_BIT_SHIFT
        plat |= lat_msk

        return 'PID %X, %X' % (plon, plat)

    def _lonstr2lon(self, lonstr):
        x = int(lonstr, 16)
        if 0 == (x & self._IDENTIFY_EWSN_MASK):
            return self._plonlatTolonlat(x)
        else:
            return - self._plonlatTolonlat(x)

    def _latstr2lat(self, latstr):
        y = int(latstr, 16)
        if 0 == (y & self._IDENTIFY_EWSN_MASK):
            return self._plonlatTolonlat(y)
        else:
            return - self._plonlatTolonlat(y)

    def _plonlatTolonlat(self, pstr):
        pstr = pstr & (~self._IDENTIFY_EWSN_MASK)

        if 0 != (pstr & self._IDENTIFY_EXTENDED_AREA_MASK):
            temp = pstr & self._IDENTIFY_EXTENDED_AREA_MASK
            pstr >>= self._IGNORE_EXTRA_BIT_SHIFT
            pstr &= ~self._IDENTIFY_EXTENDED_AREA_MASK
            pstr |= temp
        else:
            pstr >>= self._IGNORE_EXTRA_BIT_SHIFT

        return pstr / self._FACTOR

#===============================================================================
# DMS Related Converters
#===============================================================================

class DMSConverter(LonLatConverter):

    _FORMAT_NAME = 'Degrees Minutes Seconds (DMS)'

    # N/S/E/W flag is at front of DMS
    _LON_F = r'''(?P<ew>[-+EW])
                \s?
                (?P<d1>\d+)
                \s
                (?P<m1>\d+)
                \s
                (?P<s1>\d+(?:(?:\s|\.)\d*)?|\d*\.\d+)
                '''

    _LAT_F = r'''(?P<ns>[-+NS])
                \s?
                (?P<d2>\d+)
                \s
                (?P<m2>\d+)
                \s
                (?P<s2>\d+(?:(?:\s|\.)\d*)?|\d*\.\d+)
                '''

    # N/S/E/W flag is at end of DMS
    _LON_B = r'''(?P<d1>\d+)
                \s
                (?P<m1>\d+)
                \s
                (?P<s1>\d+(?:(?:\s|\.)\d*)?|\d*\.\d+)
                \s?
                (?P<ew>[EW])
                '''

    _LAT_B = r'''(?P<d2>\d+)
                \s
                (?P<m2>\d+)
                \s
                (?P<s2>\d+(?:(?:\s|\.)\d*)?|\d*\.\d+)
                \s?
                (?P<ns>[NS])
                '''

    # Build the Regex
    _PATTERN_FROM_STRINGS = [
        re.compile(r'^' + '\s?' + _LON_F + '\s' + _LAT_F + '\s?' + r'$', re.I | re.X),
        re.compile(r'^' + '\s?' + _LAT_F + '\s' + _LON_F + '\s?' + r'$', re.I | re.X),
        re.compile(r'^' + '\s?' + _LON_B + '\s' + _LAT_B + '\s?' + r'$', re.I | re.X),
        re.compile(r'^' + '\s?' + _LAT_B + '\s' + _LON_B + '\s?' + r'$', re.I | re.X),
            ]

    _rwhitespace = re.compile(r'(?:(?!\d|\.|(?<![A-Z])[-+EWNS](?![A-Z]))(?:.|\s))+', re.I)
    def _reduceWhitespace(self, s):
        return r' '.join(self._rwhitespace.split(s))

    def fromString(self, lonlat):
        match = None
        lonlat_reduced = self._reduceWhitespace(lonlat)

        for pattern in self._PATTERN_FROM_STRINGS:
            match = pattern.match(lonlat_reduced)
            if match:
                break

        if not match:
            raise LonLatConvertFailed()

        return self._matchobj2lonlat(match)

    def toString(self, lonlat):

        lon, lat = lonlat
        sig1, d1, m1, s1 = self._deg2dms(lon)
        sig2, d2, m2, s2 = self._deg2dms(lat)

        ew = 'E' if sig1 >= 0 else 'W'
        ns = 'N' if sig2 >= 0 else 'S'

        return '%s%d %d\'%.1f", %s%d %d\'%.1f"' % (ew, d1, m1, s1, ns, d2, m2, s2)

    def _matchobj2lonlat(self, match):
        lon = self._dms2deg(
            match.group('d1'),
            match.group('m1'),
            match.group('s1').replace(r' ', r'.'),
            match.group('ew')
            )

        lat = self._dms2deg(
            match.group('d2'),
            match.group('m2'),
            match.group('s2').replace(r' ', r'.'),
            match.group('ns')
            )

        return (lon, lat)

    def _dms2deg(self, d, m, s, sig):
        deg = float(d) + float(m) / 60. + float(s) / 3600.
        if sig in '-wWsS':
            deg = -deg
        return deg

    def _deg2dms(self, deg):
        sig = 1 if deg >= 0 else - 1
        deg = math.fabs(deg)

        d = math.trunc(deg)
        remain = deg - d
        m = math.trunc(round(remain * 60., 8))
        remain -= m / 60.
        if remain < 0:
            remain = 0
        s = remain * 3600.

        return sig, d, m , s

class DMSConverterLFV(DMSConverter):

    _FORMAT_NAME = 'DMS (L-Format Viewer Favour)'

    _PATTERN_FROM_STRING = re.compile(
        r'^(?P<ns>[NS]) (?P<d2>\d+) (?P<m2>\d+) (?P<s2>\d+ \d+) (?P<ew>[EW]) (?P<d1>\d+) (?P<m1>\d+) (?P<s1>\d+ \d+)$')

    def fromString(self, lonlat):
        match = self._PATTERN_FROM_STRING.match(lonlat)
        if not match:
            raise LonLatConvertFailed()

        return self._matchobj2lonlat(match)

    def _dms2deg(self, d, m, s, sig):
        s = s.replace(' ', '.', 1)
        deg = float(d) + float(m) / 60. + float(s) / 3600.
        if sig in '-wWsS':
            deg = -deg
        return deg

    def toString(self, lonlat):
        lon, lat = lonlat
        sig1, d1, m1, s1 = self._deg2dms(lon)
        sig2, d2, m2, s2 = self._deg2dms(lat)

        ew = 'E' if sig1 >= 0 else 'W'
        ns = 'N' if sig2 >= 0 else 'S'
        s1 = ('%.03f' % s1).replace('.', ' ', 1)
        s2 = ('%.03f' % s2).replace('.', ' ', 1)

        return '%s %03d %02d %s %s %03d %02d %s' % (ns, d2, m2, s2, ew, d1, m1, s1)

class DMSConverterNaviAppDispFavour(DMSConverter):

    _FORMAT_NAME = 'DMS (Navi Application Display Favour)'

    _PATTERN_FROM_STRING = re.compile(
        r'^(?P<d2>\d+)°(?P<m2>\d+)′(?P<s2>\d+\.\d+)″(?P<ns>[NS])\s+(?P<d1>\d+)°(?P<m1>\d+)′(?P<s1>\d+\.\d+)″(?P<ew>[EW])$')

    def fromString(self, lonlat):
        match = self._PATTERN_FROM_STRING.match(lonlat)
        if not match:
            raise LonLatConvertFailed()

        return self._matchobj2lonlat(match)

    def _dms2deg(self, d, m, s, sig):
        deg = float(d) + float(m) / 60. + float(s) / 3600.
        if sig in '-wWsS':
            deg = -deg
        return deg

    def toString(self, lonlat):
        lon, lat = lonlat
        sig1, d1, m1, s1 = self._deg2dms(lon)
        sig2, d2, m2, s2 = self._deg2dms(lat)

        ew = 'E' if sig1 >= 0 else 'W'
        ns = 'N' if sig2 >= 0 else 'S'

        return '%d°%d′%.01f″%s\t%d°%d′%.01f″%s' % (d2, m2, s2, ns, d1, m1, s1, ew)

class RadianConverter(LonLatConverter):

    _FORMAT_NAME = 'Radian (show only)'

    def fromString(self, lonlat):
        raise LonLatConvertFailed()

    def toString(self, lonlat):
        return '%.7f, %.7f' % tuple(map(lambda x: x / 90. * math.acos(0), lonlat))

#===============================================================================
# AnyLonLat Converter
#===============================================================================

class AnyLonLat():

    # note: list loose patterns first, then strict ones
    CONVERTER_LIST = [
        DDDConverter,
        HexConverter,
        HexConverterC,
        DMSConverterLFV,
        DMSConverterNaviAppDispFavour,
        DMSConverter,
#        WolframAlphaConverter,
        DecConverter,
        RadianConverter,
        PIDConverter,
    ]

    def __init__(self):
        self._converters = list(c() for c in self.CONVERTER_LIST)
        self._lonlat = None

    def get_lonlat(self):
        """Get converted LonLat as a float tuple"""
        return self._lonlat

    def get_format_names(self):
        """Get available format names as a iterator of string"""
        return (c.getFormatName() for c in self._converters)

    def get_convert_results(self):
        """Get convert results as a iterator of string"""
        assert self._lonlat
        return (c.toString(self._lonlat) for c in self._converters)

    def get_num_of_converters(self):
        """Get number of converters"""
        return len(self._converters)

    def convert_any_lonlat(self, any_lonlat):
        """Convert a LonLat string, return the format name of the input
        as result, return False when convert failed. """
        # iterate over converters until one gives result
        for n, converter in enumerate(self._converters):
            try:
                self._lonlat = converter.fromString(any_lonlat)
                return converter.getFormatName()
            except LonLatConvertFailed:
                pass
        else:
            # otherwise conversion is failed
            self._lonlat = None
            return False


#===============================================================================
# GUI 
#===============================================================================

class MainWindow(Frame, AnyLonLat):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        AnyLonLat.__init__(self)
        self.master = master

        self.createVariable()
        self.createWidgets()

        self.varInputLonLat.set(
            'W109 16\'36.88", S27 07\'32.46"' # Easter island :-)
            )
        self.reCalculate()

    def createVariable(self):

        self.varInputLonLat = StringVar()
        self.varInputPrompt = StringVar()
        self.varOutputs = list(StringVar() for x in range(self.get_num_of_converters()))

    def createWidgets(self):
        PAD = 3
        self.frameTop = LabelFrame(self.master, text='Input Any Lonlat')

        self.entryLonLatInput = Entry(self.frameTop, cursor='ibeam', width=78,
                                      textvariable=self.varInputLonLat)
        self.entryLonLatInput.grid(column=0, row=0, padx=PAD, pady=PAD, sticky=E + W)
        self.entryLonLatInput.bind('<Any-KeyRelease>', self.reCalculate)

        self.labelInputPrompt = Label(self.frameTop, textvariable=self.varInputPrompt)
        self.labelInputPrompt.grid(column=0, row=1, padx=PAD, pady=PAD)

        Button(self.frameTop, text='Paste', command=self.pasteInputFromClipboard).grid(column=1, row=0, padx=PAD)
        Button(self.frameTop, text='Swap', command=self.swapLonLat).grid(column=1, row=1, padx=PAD)

        self.frameOutput = LabelFrame(self.master, text='Convert Result')

        for n, converter_name in enumerate(self.get_format_names()):
            entry_var = self.varOutputs[n]
            label = converter_name + ' :'

            Label(self.frameOutput, text=label, justify=RIGHT)\
                .grid(column=0, row=n, sticky=E, padx=PAD, pady=PAD)

            entry = Entry(self.frameOutput, width=40, cursor='ibeam', state='readonly', textvariable=entry_var)
            entry.grid(column=1, row=n, sticky=W + E, padx=PAD, pady=PAD)

            def button_cb(self=self, entry=entry, entry_var=entry_var):
                self.copyOutput2Clipboard(entry, entry_var)

            button = Button(self.frameOutput, text='Copy', command=button_cb)
            button.grid(column=2, row=n, sticky=E, padx=PAD)

        self.frameBottom = Frame(self.master)

        Button(self.frameBottom, text='Show in GoogleMap',
            command=self.openGoogleMap).pack(side=LEFT, padx=PAD)

        Button(self.frameBottom, text='Show in WolframAlpha',
            command=self.openWolframAlpha).pack(side=LEFT, padx=PAD)

        Button(self.frameBottom, text='Quit',
            command=self.master.quit).pack(side=RIGHT, padx=PAD)

        self.frameTop.grid(column=0, row=0, padx=PAD, pady=PAD, sticky=W + E + N)
        self.frameOutput.grid(column=0, row=1, padx=PAD, pady=PAD, sticky=W + E)
        self.frameBottom.grid(column=0, row=2, padx=PAD, pady=PAD, sticky=W + E)
        self.frameTop.columnconfigure(0, weight=1)
        self.frameOutput.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def reCalculate(self, event=None):
        input = self.varInputLonLat.get().strip()
        format_name = self.convert_any_lonlat(input)
        if format_name: # convert success
            prompt = 'Input format is "%s"' % format_name
            self.varInputPrompt.set(prompt)
            self.entryLonLatInput.configure(foreground='black')
            for n, result in enumerate(self.get_convert_results()):
                self.varOutputs[n].set(result)

        else:
            self.entryLonLatInput.configure(foreground='red')
            self.varInputPrompt.set('Unknown format')
            for n in range(self.get_num_of_converters()):
                self.varOutputs[n].set('')

    def swapLonLat(self):
        input = self.varInputLonLat.get().strip()

        splited = tuple(map(lambda x:x.strip(), input.split(',')))
        if len(splited) != 2:
            return
        self.varInputLonLat.set('%s, %s' % (splited[1], splited[0]))
        self.reCalculate()

    def openGoogleMap(self, event=None):
        if not self._lonlat:
            return
        lon, lat = self._lonlat
        webbrowser.open('http://maps.google.com/maps?ll=%f,%f&hl=en&t=h' % (lat, lon))

    def openWolframAlpha(self, event=None):
        if not self._lonlat:
            return
        lonlat = WolframAlphaConverter().toString(self._lonlat)
        webbrowser.open('http://www.wolframalpha.com/input/?i=%s' % lonlat)

    def copyOutput2Clipboard(self, control, control_var):
        control.clipboard_clear()
        control.clipboard_append(control_var.get())

    def pasteInputFromClipboard(self):
        self.varInputLonLat.set(self.entryLonLatInput.clipboard_get())
        self.reCalculate()


def main():
    root = Tk()

    main_frame = MainWindow(root)
    main_frame.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)
    main_frame.grid(sticky=N + E + S + W)

    top_level = main_frame.winfo_toplevel()
    top_level.title('Any LonLat ' + __version__)
    top_level.rowconfigure(0, weight=1)
    top_level.columnconfigure(0, weight=1)
    top_level.resizable(False, False)

    root.mainloop()

if __name__ == '__main__':
    main()
