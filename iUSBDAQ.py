from ctypes import *
from ctypes.wintypes import DWORD, BYTE, HANDLE

class DevSession(Structure):
    _fields_ = [('DevIndex', c_int),
                ('DevInstance', c_int),
                ('DevType', c_ulong),
                ('iSession1', HANDLE),
                ('iSession2', HANDLE)]

class iUSBDAQError(Exception):
    pass

# These values taken from InDevIUSBDAQObject.pas
RATE        = 60
OVERSAMPLE  = 3
NCHANNELS   = 8
BUFFSIZE    = 128

class iUSBDAQ(object):
    '''
    ctypes interface to the iUSBDAQ driver
    '''

    # DLL helpers

    dll = CDLL('iUSBDAQ')

    class __DLLFuncs(object):
        ''' Get a function from the DLL and set up error checking '''
        def __getattr__(self, fn):
            def check(result, func, args):
                if result != 0:
                    err = create_string_buffer(256)
                    iUSBDAQ.dll.iUSBDAQ_GetErrorDes(result, err)
                    raise iUSBDAQError(err.value)

            f = getattr(iUSBDAQ.dll, 'iUSBDAQ_' + fn)
            f.restype = c_int
            f.errcheck = check
            return f
    dllfn = __DLLFuncs()

    @classmethod
    def GetDLLVersion(cls):
        fn = cls.dll.iUSBDAQ_GetDLLVersion
        fn.restype = DWORD
        return fn()

    @classmethod
    def EnumerateDev(cls):
        n = c_int()
        cls.dllfn.EnumerateDev(0, byref(n))
        return n.value

    # Connection management methods

    def __init__(self, dev=None):
        if dev is not None:
            self.OpenDevice(dev)
        else:
            self.dev = c_void_p()

        self.buff = (c_float * BUFFSIZE)()

    def __del__(self):
        try:
            self.ReleaseDevice()
        except:
            pass

    def OpenDevice(self, index=0):
        self.__dev = DevSession()
        self.dev = pointer(self.__dev)
        self.dllfn.OpenDevice(0, index, self.dev)

    def ReleaseDevice(self):
        self.dllfn.ReleaseDevice(self.dev)
        self.dev = c_void_p()

    def Reset(self):
        self.dllfn.Reset(self.dev)

    # Device information methods

    def GetDeviceSerialNo(self):
        serial = c_int()
        self.dllfn.GetDeviceSerialNo(self.dev, byref(serial))
        return serial.value

    def GetFirmwareVersion(self):
        ver = DWORD()
        self.dllfn.GetFirmwareVersion(self.dev, byref(ver))
        return ver.value

    def ReadIUSB_DEVID(self):
        devid = BYTE()
        self.dllfn.ReadIUSB_DEVID(self.dev, byref(devid))
        return devid.value

    # Streaming methods

    def AIStartStream(self, rate=RATE):
        sample_rate = rate * OVERSAMPLE * BUFFSIZE
        scan_rate = sample_rate / NCHANNELS
        actual_rate = c_int()
        self.dllfn.AIStartStream(self.dev, 0, NCHANNELS, 0,
                                 scan_rate, byref(actual_rate),
                                 False)

        actual = (actual_rate.value * NCHANNELS) / (BUFFSIZE * OVERSAMPLE)

        if actual != scan_rate:
            print 'ERROR: Actual sample rate differs from requested rate'
            print 'Requested', scan_rate, 'got', actual

    def AIStopStream(self):
        self.dllfn.AIStopStream(self.dev)

    def AIGetScans(self, timeout=1000):
        nsamp = BUFFSIZE / NCHANNELS
        actual_samp = c_int()
        self.dllfn.AIGetScans(self.dev, nsamp, timeout,
                              byref(self.buff), byref(actual_samp))
        return actual_samp.value

    # Helper methods

    @classmethod
    def VoltToBits(cls, voltage):
        v2b = cls.dll.iUSBDAQ_VoltToBits
        v2b.argtypes = [c_float]
        v2b.restype = c_int
        return v2b(voltage)

    @classmethod
    def BitsToVolt(cls, bits):
        b2v = cls.dll.iUSBDAQ_BitsToVolt
        b2v.argtypes = [c_int]
        b2v.restype = c_float
        return b2v(bits)

