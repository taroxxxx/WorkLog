# -*- coding: utf-8 -*-

"""
.. note::
"""

import os

from PySide import QtCore


class Signal( QtCore.QObject ):

    stop_app_signal = QtCore.Signal()


class ServerInstance():

    def __init__( self, parent=None ):

        # Signal
        self.signal = Signal()


    def is_alive( self ):

        return 1 # just check return


    def stop_app( self ):

        self.signal.stop_app_signal.emit()

        return 1


    def get_app_pid( self ):

        return os.getpid() # pid
