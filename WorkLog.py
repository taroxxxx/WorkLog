# -*- coding: utf-8 -*-

'''
WorkLog.py

written by : taro matsuura
(C)2020 DandeLionAnimationStudio,LLC

MODIFY THIS AT YOUR OWN RISK !
'''

import sys
import logging
import traceback

from PySide import QtCore, QtGui

if __name__ == '__main__':

    try:
        from worklog_main import Main

        app = QtGui.QApplication( sys.argv )

        main = Main( app )
        main.start()
        sys.exit( app.exec_() )

    except SystemExit:
        pass

    except:
        logging.error( traceback.format_exc() )

    	if not hasattr( sys, 'frozen' ):
    		raw_input( '---' )
