# -*- coding: utf-8 -*-

"""
.. note::
"""

from PySide import QtCore, QtGui


class Combobox( QtGui.QDialog ):

    def __init__( self, parent=None, editable=0 ):
        super( Combobox, self ).__init__( parent )

        self.combobox_item = None

        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint| QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint
        )

        self.combobox = QtGui.QComboBox( self )
        self.combobox.setEditable( editable )

        self.pushbutton_ok = QtGui.QPushButton( self )
        self.pushbutton_ok.setText( 'Ok' )

        spacer = QtGui.QSpacerItem( 0, 0, QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Expanding )

        v_layout = QtGui.QVBoxLayout( self )
        v_layout.addWidget( self.combobox )
        v_layout.addWidget( self.pushbutton_ok )
        v_layout.addItem( spacer )

        self.pushbutton_ok.pressed.connect( self.signal_func_pushbutton_ok_pressed )


    def add_items( self, list, index ):

        """
        # addItems
        """

        self.combobox.clear()
        self.combobox.addItems( list )
        self.combobox.setCurrentIndex( index )

        return


    def get_combobox_item( self ):

        return self.combobox_item


    @QtCore.Slot()
    def signal_func_pushbutton_ok_pressed( self ):

        """
        # get currentText

        >>> self.pushbutton_ok.pressed
        """

        self.combobox_item = self.combobox.currentText()
        self.close()

        return
