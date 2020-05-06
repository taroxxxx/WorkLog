# -*- coding: utf-8 -*-

"""
.. note::
"""

import time
import datetime

from PySide import QtCore, QtGui


class Signal( QtCore.QObject ):

    # worklog_main / signal_func_create_html
    main_create_html_signal = QtCore.Signal( str, datetime.datetime, int )


class Calendar( QtGui.QDialog ):

    def __init__( self, parent=None ):
        super( Calendar, self ).__init__( parent )

        """
        # Calendar ダイアログ
        """

        # Signal
        self.signal = Signal()

        self.cur_year = None
        self.cur_month = None

        self.target_datetime = None

        self.has_data_date_list = []

        self.has_data_chfmt = QtGui.QTextCharFormat()
        #self.has_data_chfmt.setFont( QtGui.QFont( 'Arial', 12 ) )
        self.has_data_chfmt.setFontUnderline( 1 )
        self.has_data_chfmt.setFontWeight( QtGui.QFont.Bold )

        self.setWindowTitle( 'Calendar' )

        self.calendar = QtGui.QCalendarWidget( self )

        self.calendar.setGridVisible( 1 )
        #self.calendar.setNavigationBarVisible( 0 )
        self.calendar.setFirstDayOfWeek( QtCore.Qt.Monday )

        self.calendar.setHorizontalHeaderFormat ( QtGui.QCalendarWidget.ShortDayNames )
        self.calendar.setVerticalHeaderFormat( QtGui.QCalendarWidget.NoVerticalHeader )

        today_datetime = datetime.date.today()

        self.pushbutton_day = QtGui.QPushButton( self )
        self.pushbutton_day.setText( 'Day' )

        self.pushbutton_week = QtGui.QPushButton( self )
        self.pushbutton_week.setText( 'Week' )

        self.pushbutton_month = QtGui.QPushButton( self )
        self.pushbutton_month.setText( 'Month' )

        layout = QtGui.QVBoxLayout( self )
        layout.addWidget( self.calendar )
        layout.addWidget( self.pushbutton_day )
        layout.addWidget( self.pushbutton_week )
        layout.addWidget( self.pushbutton_month )

        self.calendar.clicked.connect( self.signal_func_calendar_clicked )
        self.calendar.currentPageChanged.connect( self.signal_func_calendar_currentPageChanged )

        self.pushbutton_day.pressed.connect( self.signal_func_pushbutton_day_pressed )
        self.pushbutton_week.pressed.connect( self.signal_func_pushbutton_week_pressed )
        self.pushbutton_month.pressed.connect( self.signal_func_pushbutton_month_pressed )


    def set_cur_year_month( self, year, month ):

        """
        # cur_year, cur_month の設定

        i@year :
        i@month :
        """

        self.cur_year = year
        self.cur_month = month

        return


    def update_calendar( self ):

        """
        # Calendar の初期設定
        """

        for date_item in self.has_data_date_list:
            qdate = QtCore.QDate( *date_item )
            self.calendar.setDateTextFormat( qdate, self.has_data_chfmt )

        maximum_date_item = self.has_data_date_list[-1]
        maximum_qdate = QtCore.QDate( *maximum_date_item )
        self.calendar.setMaximumDate( maximum_qdate )

        minimum_date_item = self.has_data_date_list[0]
        minimum_qdate = QtCore.QDate( *minimum_date_item )
        self.calendar.setMinimumDate(minimum_qdate )

        # set today
        d = datetime.datetime.fromtimestamp( time.time() )
        time_today_start = time.mktime( datetime.datetime( d.year, d.month, d.day, 0,0,0 ).timetuple() )

        self.target_datetime = datetime.datetime.fromtimestamp( time_today_start )
        self.calendar.setSelectedDate( QtCore.QDate( d.year, d.month, d.day ) )

        return


    @QtCore.Slot( list )
    def signal_func_set_has_data_date_list( self, list ):

        """
        # self.has_data_date_list の設定
        @list

        >>> worklog_main_thread.signal.calendar_set_has_data_date_item_list_signal
        """

        self.has_data_date_list = list

        return


    @QtCore.Slot( QtCore.QDate )
    def signal_func_calendar_clicked( self, qdate ):

        """
        # self.target_datetime の設定
        @qdate

        >>> self.calendar.clicked.
        """

        target_time = time.mktime( datetime.datetime( qdate.year(), qdate.month(), qdate.day(), 0,0,0 ).timetuple() )
        self.target_datetime = datetime.datetime.fromtimestamp( target_time )

        return


    @QtCore.Slot( int, int )
    def signal_func_calendar_currentPageChanged( self, year, month ):

        """
        # self.set_cur_year_month

        i@year
        i@month

        >>> self.calendar.currentPageChanged
        """

        self.set_cur_year_month( year, month )

        return


    @QtCore.Slot()
    def signal_func_pushbutton_day_pressed( self ):

        """
        # self.signal.main_create_html_signal > signal_func_create_html
        """

        self.signal.main_create_html_signal.emit(
            'specified_date', self.target_datetime, 0
        )

        return


    @QtCore.Slot()
    def signal_func_pushbutton_week_pressed( self ):

        """
        # self.signal.main_create_html_signal > signal_func_create_html
        """

        self.signal.main_create_html_signal.emit(
            'specified_week', self.target_datetime, 1
        )

        return


    @QtCore.Slot()
    def signal_func_pushbutton_month_pressed( self ):

        """
        # self.signal.main_create_html_signal > signal_func_create_html
        """

        self.signal.main_create_html_signal.emit(
            'month', self.target_datetime, 0
        )

        return


    @QtCore.Slot( int, int )
    def signal_func_set_cur_year_month( self, year, month ):

        """
        # self.set_cur_year_month

        i@year
        i@month

        >>> main_thread.signal.calendar_set_cur_year_month_signal
        """

        self.set_cur_year_month( year, month )

        return
