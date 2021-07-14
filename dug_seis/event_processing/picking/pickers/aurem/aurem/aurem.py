import logging
import numpy as np
import pathlib
import ctypes as C
import copy
from obspy import UTCDateTime
#
from aurem import plotting as AUPL

logger = logging.getLogger(__name__)


# -------------------------------------------  Load and Setup C library
MODULEPATH = pathlib.Path(__file__).parent.absolute()

libname = tuple(MODULEPATH.glob("src/aurem_clib.*.so"))[0]
myclib = C.CDLL(libname)

# AIC
myclib.aicp.restype = C.c_int
myclib.aicp.argtypes = [np.ctypeslib.ndpointer(
                                        dtype=np.float32, ndim=1,
                                        flags='C_CONTIGUOUS'), C.c_int,
                        # OUT
                        np.ctypeslib.ndpointer(
                                        dtype=np.float32, ndim=1,
                                        flags='C_CONTIGUOUS'),
                        C.POINTER(C.c_int)]

# REC
myclib.recp.restype = C.c_int
myclib.recp.argtypes = [np.ctypeslib.ndpointer(
                                        dtype=np.float32, ndim=1,
                                        flags='C_CONTIGUOUS'), C.c_int,
                        # OUT
                        np.ctypeslib.ndpointer(
                                        dtype=np.float32, ndim=1,
                                        flags='C_CONTIGUOUS'),
                        C.POINTER(C.c_int)]
# ---------------------------------------------------------------------


class REC(object):
    """ This class initialize the Reciprocal-Based Picker algorithm.
        The picker takes in inputs only the obspy.Stream objects.
        Being completely automatic, only the channel parameter to
        specify the working trace is accepted.
    """
    def __init__(self, trace):
        #self.st = stream.copy()
        #self.wt = self.st.select(channel=channel)[0]
        self.wt = trace
        #
        self.recfn = None
        self.idx = None
        self.pick = None

    def _calculate_rec_cf(self):
        """ Create the
        This method will return the Reciprocal-Based carachteristic
        function, that will be analyzed in the `work` method.

        Inputs:
            arr must be a  `numpy.ndarray`

        """
        if not isinstance(self.wt.data, np.ndarray):
            raise ValueError("Input time series must be a numpy.ndarray instance!")
        self.recfn = np.zeros(self.wt.data.size - 1)
        arr = self.wt.data

        with np.errstate(divide='raise'):
            for ii in range(1, arr.size):
                try:
                    val1 = ii/(np.var(arr[0:ii]))
                except FloatingPointError:  # if var==0 --> log is -inf
                    val1 = 0.00  # orig
                try:
                    val2 = (arr.size - ii)/np.var(arr[ii:])
                except FloatingPointError:  # if var==0 --> log is -inf
                    val2 = 0.00  # orig
                self.recfn[ii-1] = (-val1-val2)

    def work(self):
        """ This method will create the CF and return the index
            responding to the minimum of the CF.

        """
        self._calculate_rec_cf()
        # (ascending order min->max) OK!
        self.idx = np.nanargmin(self.recfn)   # NEW
        self.pick = (self.wt.stats.starttime +
                     self.wt.stats.delta * self.idx)

    def set_working_trace(self, channel):
        if not isinstance(channel, str):
            raise TypeError
        #
        self.wt = self.st.select(channel=channel)[0]

    def get_rec_function(self):
        if isinstance(self.recfn, np.ndarray) and self.recfn.size > 0:
            return self.recfn
        else:
            logger.warning("Missing EVALUATION FUNCTION! " +
                           "Run the work method first!")

    def get_pick_index(self):
        if self.idx:
            return self.idx
        else:
            logger.warning("Missing INDEX! " +
                           "Run the work method first!")

    def get_pick(self):
        if self.pick:
            if isinstance(self.pick, UTCDateTime):
                return self.pick
            else:
                raise TypeError
        else:
            logger.warning("Missing PICK! " +
                           "Run the work method first!")

    def plot(self):
        """ Wrapper around the plot_rec function in plot method

        """
        AUPL.plot_rec(self,
                      plot_ax=None,
                      plot_cf=True,
                      plot_pick=True,
                      plot_additional_picks={},
                      normalize=True,
                      axtitle="REC picks",
                      show=True)


class AIC(object):
    """ This class initialize the Akaike Information Criteria Picker
        algorithm. The picker takes in inputs only the obspy.Stream
        objects. Being completely automatic, only the channel parameter
        to specify the working trace is accepted.
    """
    # def __init__(self, stream, channel="*Z"):
    def __init__(self, trace):
        #self.st = stream.copy()
        #self.wt = self.st.select(channel=channel)[0]
        self.wt = trace
        #
        self.aicfn = None
        self.idx = None
        self.pick = None

    def _calculate_aic_cf(self):
        """
        Differently from AR-AIC picker, this function calculates AIC function
        directly from the data, without using the AR coefficients (Maeda, 1985)

        Computes P-phase arrival time digital single-component acceleration
        or broadband velocity record without requiring threshold settings using
        AKAIKE INFORMATION CRITERION.
        Returns P-phase arrival time index and the characteristic function.
        The returned index correspond to the characteristic function's minima.

        Inputs:
            arr must be a  `numpy.ndarray`

        References:
            [Maeda1985]

        """
        if not isinstance(self.wt.data, np.ndarray):
            raise ValueError("Input time series must be a numpy.ndarray instance!")
        self.aicfn = np.zeros(self.wt.data.size - 1)
        arr = self.wt.data
        # --------------------  CF calculation
        with np.errstate(divide='raise'):
            for ii in range(1, arr.size):
                try:
                    var1 = np.log(np.var(arr[0:ii]))
                except FloatingPointError:  # if var==0 --> log is -inf
                    var1 = 0.00
                #
                try:
                    var2 = np.log(np.var(arr[ii:]))
                except FloatingPointError:  # if var==0 --> log is -inf
                    var2 = 0.00
                #
                val1 = ii * var1
                val2 = (arr.size - ii - 1) * var2
                self.aicfn[ii - 1] = (val1 + val2)
        return True

    # def work_old(self):
    #     """ This method will create the CF and return the index
    #         responding to the minimum of the CF.

    #     """
    #     self._calculate_aic_cf()   # create self.aicfn
    #     self.idx = np.nanargmin(self.aicfn)   # NEW
    #     self.pick = (self.wt.stats.starttime +
    #                  self.wt.stats.delta * self.idx)

    def work(self):
        """ This method will create the CF and return the index
            responding to the minimum of the CF.

            Now the calculation of CF and extraction of index is
            done into a function C-implemented !!!
        """
        pminidx = C.c_int()
        tmparr = np.ascontiguousarray(self.wt.data, np.float32)
        self.aicfn = np.zeros(self.wt.data.size - 1,
                              dtype=np.float32, order="C")
        ret = myclib.aicp(tmparr, self.wt.data.size,
                          self.aicfn, C.byref(pminidx))
        if ret != 0:
            raise MemoryError("Something wrong with AIC picker C-routine")
        #
        self.idx = pminidx.value
        if self.idx != 0 and isinstance(self.idx, int):
            # pick found
            logger.debug("AIC found pick")
            self.pick = (self.wt.stats.starttime +
                         self.wt.stats.delta * self.idx)
        else:
            # if idx == 0, it means inside C routine it didn't pick
            logger.debug("AIC didn't found pick")
            self.pick = None

    def set_working_trace(self, channel):
        if not isinstance(channel, str):
            raise TypeError
        #
        self.wt = self.st.select(channel=channel)[0]

    def get_aic_function(self, mode="real"):
        """
        mode could be either 'real' or 'plot' (for matplotlib etc..).
        Mode PLOT return a deepcopy modified of the real one
        """
        if isinstance(self.aicfn, np.ndarray) and self.aicfn.size > 0:
            if mode.lower() == 'real':
                return self.aicfn
            elif mode.lower() == 'plot':
                _wa = copy.deepcopy(self.aicfn)
                # GoingToC: replace INF at the start and end with adiacent
                #           values for plotting reasons
                _wa[0] = _wa[1]
                _wa[-1] = _wa[-2]
                return _wa
            raise ValueError("Mode must be either 'real' or 'plot'")
        else:
            raise AttributeError("Missing EVALUATION FUNCTION! " +
                                 "Run the work method first!")

    def get_pick_index(self):
        if self.idx is None:
            raise AttributeError("Missing INDEX! " +
                                 "Run the work method first!")
        #
        if isinstance(self.idx, int):
            return self.idx
        else:
            raise TypeError("INDEX is not an integer: %s" %
                            str(type(self.idx)))

    def get_pick(self):
        if self.idx is None:
            raise AttributeError("Missing PICK! " +
                                 "Run the work method first!")
        else:
            # At this stage, it can be already UTCDateTime or None.
            # Work method took car
            return self.pick

    def plot(self):
        """ Wrapper around the plot_aic function in plot method

        """
        AUPL.plot_aic(self,
                      plot_ax=None,
                      plot_cf=True,
                      plot_pick=True,
                      plot_additional_picks={},
                      normalize=True,
                      axtitle="AIC picks",
                      show=True)
