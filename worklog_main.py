# -*- coding: utf-8 -*-

"""
.. note::
"""

import os
import re
import sys
import json
import time
import psutil
import signal
import socket
import logging
import datetime
import traceback
import xmlrpclib
import logging.handlers

import win32api

from functools import partial
from PySide import QtCore, QtGui

from worklog_main_thread import MainThread
from worklog_server_thread import ServerThread
from worklog_server_instance import ServerInstance

from worklog_dlg_calendar import Calendar
from worklog_dlg_combobox import Combobox

import _lib
import _sqlite
import _analysis


class Main( QtGui.QWidget ):

    def __init__( self, app, parent=None ):
        super( Main, self ).__init__( parent )

        self.app = app
        self.app_name = 'WorkLog'

        ### SETTINGS ###
        frozen = hasattr( sys, 'frozen' )

        #frozen = 1 # dev

        is_away_min = 10 if frozen else 5 # 離席と判定するまでの時間 (min)
        interval_sec = 60 if frozen else 30 # データの取得間隔 (sec)
        self.port_no = 52001 if frozen else 52002 # dev

        ignore_drive_list = [ 'A','C','D','U','V','X' ] # drives not to get project name from window path

        # '|' で分離された正規表現は左から右へ順に試されます
        ext_list = [
            'hiplc', 'hipnc', 'hip',
            'nk',
            'ma', 'mb',
            'aep',
            'blend',
            'pyw', 'py',
            'txt', 'loq', 'env', 'shelf',
            'html', 'xml', 'json',
        ]

        # get project primary
        pri_file_path_fmt = re.compile( r'(?P<drive>[\w]):/(?P<project>[\w]+)/' )

        # get project 2nd
        sec_file_path_fmt_list = [
            re.compile( r'/(Project)/(?P<project>[\w]+)/' ),
            re.compile( r'/(?P<project>(Development))[\s/]' ),
            re.compile( r'/[_]*(?P<project>(RnD))/' ),
        ]

        # apply preset
        json_file_path = os.path.join( os.getcwd(), 'worklog.ini' )

        preset_dict = {}
        if os.path.isfile( json_file_path ):
            with open( json_file_path, 'r' ) as f:
                preset_dict = json.load( f )

        if preset_dict.has_key( 'pri_file_path_fmt' ):
            pri_file_path_fmt = re.compile( preset_dict[ 'pri_file_path_fmt' ] )

        # get file
        file_name_fmt = re.compile( r'(?P<filename>[\w.,-]*)[.](?P<ext>(?:{0})+)'.format( '|'.join(ext_list ) ) )

        # workstate project
        self.current_project = None

        # workstate dialog
        self.workstate_dlg_msg = 'Select Your Work State'
        self.workstate_item_list = [ 'Office Work', 'Remote Work', 'Private Use' ]
        self.workstate_current_index  = 1

        # project dialog
        self.project_dlg_msg = 'Select Current Project'

        # away dialog
        self.away_dlg_msg = 'Was Away from Seat... What were you doing ?'
        self.rest_time_name = 'Rest Time' # 'Work ( e.g.: Meeting )',
        self.other_project_name = 'other'

        leave_seat_name = 'Leave Seat'
        self.active_project_list = []

        # sqlite
        self.db_data_tbl_name = _sqlite.get_sqlite_tbl_name()
        self.db_data_tbl_name_item_list = _sqlite.get_sqlite_tbl_name_item_list()

        self.db_dir_path = os.path.join( os.getcwd(), 'sqlite' )

        self.db_basename_temp = 'WorkLog_{0}{1:02d}.sqlite'
        self.db_file_path = None

        log_file_path = os.path.join( os.getcwd(), 'log', 'WorkLog.log' )
        self.html_file_path = os.path.join( os.getcwd(), 'html', 'WorkLog.html' )

        # icon
        self.icon_path_app = 'icon/app.png'
        self.icon_path_tasklog = 'icon/WorkLog.png'
        self.icon_path_today = 'icon/today.png'
        self.icon_path_week = 'icon/week.png'
        self.icon_path_project = 'icon/project.png'
        self.icon_path_calendar = 'icon/calendar.png'
        self.icon_path_workstate = 'icon/workstate.png'
        self.icon_path_settings = 'icon/settings.png'
        self.icon_path_working = 'icon/working.png'
        self.icon_path_exit = 'icon/exit.png'

        ##### dialog #####
        self.resize( 0, 0 )

        dlg_size = [ 250, 50 ]

        self.display_size = (
            win32api.GetSystemMetrics(0),
            win32api.GetSystemMetrics(1),
        )

        # Calendar QDialog
        self.calendar_dlg = Calendar( self )
        self.calendar_dlg.signal.main_create_html_signal.connect( self.signal_func_create_html )

        # ComboBox QDialog
        self.combobox_dlg = Combobox( self )

        ##### IP ADDRESS #####
        ip_address = None

        ip_list = socket.gethostbyname_ex( socket.gethostname() )[2]

        if len( ip_list ) == 1:

            ip_address = socket.gethostbyname( socket.gethostname() )

        else:
            mac_address = _get_mac_address()

            for ip in ip_list:

                if getmac.get_mac_address(ip=ip).replace(':', '-').upper() == mac_address:

                    ip_address = ip

        self.ip_address = ip_address

        ##### LOG #####
        log_dir_path = os.path.dirname( log_file_path )
        if not os.path.isdir( log_dir_path ):
            os.makedirs( log_dir_path )

        """
        if os.path.isfile( log_file_path ): # reset log file
            with open( log_file_path, 'w' ) as f:
                f.write( '' )
        """

        level = logging.DEBUG
        max_bytes = 524288 # = 512 KB
        backup_count = 3

        # root logger
        logging.getLogger().setLevel( logging.DEBUG )

        # StreamHandler
        root_log_stream_handler = logging.StreamHandler()
        logging.getLogger().addHandler( root_log_stream_handler )

        # RotatingFileHandler
        root_log_rot_file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            encoding='utf-8',
            maxBytes=max_bytes,
            backupCount=backup_count
        )

        root_log_rot_file_handler.setLevel( level )
        root_log_rot_file_handler.setFormatter(
            logging.Formatter( '%(levelname)s @ %(filename)s : %(asctime)s\r\n%(message)s\r\n' )
        )

        logging.getLogger().addHandler( root_log_rot_file_handler )

        # MainThread
        self.main_thread = MainThread(
            self.db_dir_path, self.db_basename_temp,
            is_away_min, interval_sec,
            self.db_data_tbl_name,
            pri_file_path_fmt, sec_file_path_fmt_list,
            file_name_fmt,
            ignore_drive_list,
            self.rest_time_name, leave_seat_name, self.other_project_name
        )

        # connect MainThread Signal
        self.main_thread.signal.main_show_away_dialog_signal.connect( self.signal_func_show_away_dialog )
        self.main_thread.signal.main_show_workstate_dialog_signal.connect( self.signal_func_show_workstate_dialog )
        self.main_thread.signal.main_set_db_file_path_signal.connect( self.signal_func_set_db_file_path )
        self.main_thread.signal.main_set_current_project_signal.connect( self.signal_func_set_current_project )
        self.main_thread.signal.main_set_active_project_list_signal.connect( self.signal_func_set_active_project_list )

        self.main_thread.signal.calendar_set_has_data_date_item_list_signal.connect(
            self.calendar_dlg.signal_func_set_has_data_date_list
        )
        self.main_thread.signal.calendar_set_cur_year_month_signal.connect(
            self.calendar_dlg.signal_func_set_cur_year_month
        )

        # ServerInstance
        server_instance = ServerInstance()
        server_instance.signal.stop_app_signal.connect( self.signal_func_stop )

        # ServerThread
        self.server_thread = ServerThread( self.ip_address, self.port_no, server_instance  )

        # QSystemTrayIcon
        self.tray_icon = QtGui.QSystemTrayIcon()
        self.tray_icon.activated.connect( self.signal_func_tray_icon_activated )

        # QAction メニューで現在の状態を表示
        text_font = QtGui.QFont()
        text_font.setPointSize( 12 )
        text_font.setBold( 1 )

        self.cur_workstate_project_act = QtGui.QAction( QtGui.QIcon( self.icon_path_working ), '', self )
        self.cur_workstate_project_act.setFont( text_font )


    def menu_cmd_show_data( self, type_str ):

        """
        # Chart 表示

        s@type_str : 表示期間 day, week, month
        """

        _analysis.create_html(
            self.db_dir_path,
            self.db_data_tbl_name,
            self.db_data_tbl_name_item_list,
            self.html_file_path,
            self.rest_time_name,
            type=type_str,
        )

        return


    def show_combobox_dialog( self, type='workstate' ):

        """
        # Combobox

        s@type : workstate, project, away
        """

        try:

            if not self.isVisible(): # QWidget を表示しないと Dialog と一緒に終了する？
                self.show()

            if self.combobox_dlg.isVisible():
                return

            if type=='workstate':

                self.combobox_dlg.add_items(
                    self.workstate_item_list,
                    self.workstate_current_index
                )

                self.combobox_dlg.setWindowTitle( self.workstate_dlg_msg )

            elif type=='project':

                prj_item_list = _sqlite.get_lecent_project_list(
                    self.db_dir_path,
                    [ self.rest_time_name, self.other_project_name ]
                )

                prj_item_list.append( self.other_project_name ) # add other

                self.combobox_dlg.add_items(
                    prj_item_list,
                    prj_item_list.index( self.current_project )
                )

                self.combobox_dlg.setWindowTitle( self.project_dlg_msg )

            elif type=='away':

                menu_item_list = [ self.rest_time_name ] + self.active_project_list + [ self.other_project_name ]
                menu_item_list = [ item for item in set( menu_item_list ) ]

                self.combobox_dlg.add_items( menu_item_list, 0 )

                self.combobox_dlg.setWindowTitle( self.away_dlg_msg )

            self.combobox_dlg.resize( 300, 100 )
            cur_size = self.combobox_dlg.size()

            if type in [ 'workstate', 'project' ]:

                self.combobox_dlg.move(
                    self.display_size[0]*0.5 - cur_size.width()*0.5,
                    self.display_size[1]*0.5 - (cur_size.height()+30.0)*0.5 # title bar height = 30.0
                )

            elif type in [ 'away' ]:

                self.combobox_dlg.move(
                    self.display_size[0] - (cur_size.width()),
                    self.display_size[1] - (cur_size.height()+30.0) # title bar height = 30.0
                )

            self.combobox_dlg.exec_()
            combobox_item = self.combobox_dlg.get_combobox_item()

            if type=='workstate':

                self.workstate_current_index = self.workstate_item_list.index( combobox_item )
                self.main_thread.set_workstate( self.workstate_current_index )

            elif type=='project':

                self.current_project = combobox_item
                self.main_thread.set_prev_project( combobox_item )

            elif type=='away':

                self.main_thread.set_away_dlg_item( combobox_item )

            self.main_thread.set_wait( 0 )

            self.hide()

        except:

            logging.error( traceback.format_exc() )


    def menu_cmd_show_calendar( self ):

        """
        # Calendar
        """

        try:

            if not self.isVisible():
                self.show()

            if self.combobox_dlg.isVisible():
                return

            year, month = self.main_thread.get_cur_year_month()
            self.calendar_dlg.set_cur_year_month( year, month )

            self.calendar_dlg.update_calendar()

            self.calendar_dlg.resize( 232, 264 )
            cur_size = self.calendar_dlg.size()

            cursor_p = QtGui.QCursor.pos()

            self.calendar_dlg.move(
                cursor_p.x() - (cur_size.width()*0.5),
                cursor_p.y() - (cur_size.height()+30.0) # title bar height = 30.0
            )

            self.calendar_dlg.exec_()

        except:

            logging.error( traceback.format_exc() )

        return


    def menu_cmd_show_project_dialog( self ):

        """
        # project dialog
        """

        self.show_combobox_dialog( type='project' )
        return


    def menu_cmd_exit( self ):

        """
        # exit
        """

        self.stop()

        return


    def build_menu( self ):

        """
        # Context Menu
        """

        show_today_data_act = QtGui.QAction(
            QtGui.QIcon( QtGui.QPixmap( self.icon_path_today ) ),
            'Today', self,
            triggered=partial( self.menu_cmd_show_data, 'today' )
        )

        show_previousday_data_act = QtGui.QAction(
            QtGui.QIcon(),
            'Previous Day', self,
            triggered=partial( self.menu_cmd_show_data, 'previousday' )
        )

        show_thisweek_data_act = QtGui.QAction(
            QtGui.QIcon( QtGui.QPixmap( self.icon_path_week ) ),
            'This Week', self,
            triggered=partial( self.menu_cmd_show_data, 'thisweek' )
        )

        show_previousweek_data_act = QtGui.QAction(
            QtGui.QIcon(),
            'Previous Week', self,
            triggered=partial( self.menu_cmd_show_data, 'previousweek' )
        )

        show_calendar_act = QtGui.QAction(
            QtGui.QIcon( QtGui.QPixmap( self.icon_path_calendar ) ),
            'Calendar', self,
            triggered=partial( self.menu_cmd_show_calendar )
        )

        show_project_dlg_act = QtGui.QAction(
            QtGui.QIcon( QtGui.QPixmap( self.icon_path_project ) ),
            'Change Project', self,
            triggered=partial( self.menu_cmd_show_project_dialog )
        )

        show_workstate_dlg_act = QtGui.QAction(
            QtGui.QIcon( QtGui.QPixmap( self.icon_path_workstate ) ),
            'Change WorkState', self,
            triggered=partial( self.show_combobox_dialog, 'workstate' )
        )

        exit_act = QtGui.QAction(
            QtGui.QIcon( QtGui.QPixmap( self.icon_path_exit ) ),
            'Exit', self,
            triggered=partial( self.menu_cmd_exit )
        )

        menu = QtGui.QMenu()

        menu_option = QtGui.QMenu( menu )
        menu_option.setTitle( 'Edit' )
        menu_option.setIcon( QtGui.QIcon( QtGui.QPixmap( self.icon_path_settings ) ) )

        menu_option.addAction( show_project_dlg_act )
        menu_option.addSeparator()
        menu_option.addAction( show_workstate_dlg_act )

        menu_app = QtGui.QMenu( menu )
        menu_app.setTitle( 'File' )
        menu_app.setIcon( QtGui.QIcon( QtGui.QPixmap( self.icon_path_app ) ) )

        menu_app.addAction( exit_act )

        # add menu Action
        menu.addAction( self.cur_workstate_project_act )

        menu.addSeparator()

        menu.addAction( menu_option.menuAction() )

        menu.addSeparator()

        menu.addAction( show_calendar_act )

        menu.addSeparator()

        menu.addAction( show_previousweek_data_act )
        menu.addAction( show_thisweek_data_act )
        menu.addSeparator()
        menu.addAction( show_previousday_data_act )
        menu.addAction( show_today_data_act )

        menu.addSeparator()

        menu.addAction( menu_app.menuAction() )

        self.tray_icon.setContextMenu( menu )

        return


    def start( self ):

        def get_exception_err_msg( except_inst ):

            """
            # Exception を分類

            s@except_inst : Exception
            """

            err_msg = str( except_inst ).decode( 'shift_jis' )

            errno_format = re.compile( '\[Errno (?P<no>\d+)\]')
            errno_search = errno_format.search( err_msg )

            if errno_search != None:

                errno = int( errno_search.group( 'no' ) )

                if errno == 10054: # [Errno 10054] 既存の接続はリモート ホストに強制的に切断されました。
                    return 'WELL-KNOWN-ERROR - [Errno {0}] connection force disconnected.'.format( errno )

                elif errno == 10061: # [Errno 10061] 対象のコンピューターによって拒否されたため、接続できませんでした。
                    return 'WELL-KNOWN-ERROR - [Errno {0}] connection refused.'.format( errno )

                """
                if errno == 11001:
                    return '[Errno {0}] getaddrinfo failed.'.format( errno )
                """

            return None


        def killProcessTree2(pid, including_parent=True): # from : dlasLab/BatchLion/bllib/_windows.py
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                child.kill()
            psutil.wait_procs(children, timeout=5)
            if including_parent:
                parent.kill()
                parent.wait(timeout=5)

        self.setWindowFlags( QtCore.Qt.WindowStaysOnTopHint ) # for dialog


        # check Server
        try:
            url = 'http://{0}:{1}'.format( self.ip_address, self.port_no )

            server_proxy = xmlrpclib.ServerProxy( url )
            server_proxy.is_alive()

            logging.error( u'WorkLog is already running.' )

            app_pid = server_proxy.get_app_pid()
            server_proxy.stop_app()

            start_time = time.time()

            while server_proxy.is_alive():
                if time.time() - start_time > 10.0:
                    logging.warning( u'TIME OUT' )
                    break

                time.sleep( 0.1 )

            try:
                killProcessTree2( app_pid )
                logging.error( u'!!!!! Kill WorkLog Process Tree !!!!!' )

            except Exception as except_inst:
                logging.error( _lib.to_unicode( traceback.format_exc() ) )

        except Exception as except_inst:

            err_msg = get_exception_err_msg( except_inst )

            if err_msg != None:
                logging.info( err_msg )
            else:
                logging.error( _lib.to_unicode( traceback.format_exc() ) )

        self.build_menu()

        self.tray_icon.setIcon( QtGui.QIcon( QtGui.QPixmap( self.icon_path_tasklog ) ) )
        self.tray_icon.show()

        # start thread
        self.server_thread.start()
        self.main_thread.start()


    def stop( self ):

        self.main_thread.stop()

        while self.main_thread.isRunning():
            pass

        try:
            logging.shutdown()
        except:
            pass

        self.tray_icon.hide()

        # quit app
        self.app.quit()

        sys.exit( 0 )

        return


    @QtCore.Slot( QtGui.QSystemTrayIcon.ActivationReason )
    def signal_func_tray_icon_activated( self, reason ):

        """
        # TrayIcon クリック時

        @reason :
        """

        if reason == QtGui.QSystemTrayIcon.Context: # menu が表示される前

            self.cur_workstate_project_act.setText(
                '{0} - {1}'.format( self.current_project, self.workstate_item_list[ self.workstate_current_index ] )
            )

        return


    @QtCore.Slot( str )
    def signal_func_set_current_project( self, item ):

        """
        # self.current_project

        s@item :
        """

        self.current_project = item
        return


    @QtCore.Slot()
    def signal_func_show_workstate_dialog( self ):

        """
        # workstate dialog
        """

        self.show_combobox_dialog( type='workstate' )
        return


    @QtCore.Slot()
    def signal_func_show_away_dialog( self ):

        """
        # away dialog
        """

        self.show_combobox_dialog( type='away' )
        return


    @QtCore.Slot( str )
    def signal_func_set_db_file_path( self, file_path ):

        """
        # self.db_file_path

        s@file_path :
        """

        self.db_file_path = file_path

        return


    @QtCore.Slot( list )
    def signal_func_set_active_project_list( self, active_project_list ):

        """
        # self.active_project_list

        s[]@active_project_list :
        """

        self.active_project_list = active_project_list

        return


    @QtCore.Slot( int, int, str, datetime.datetime )
    def signal_func_create_html( self, type_str, target_datetime ):

        """
        # self.active_project_list

        s@type : 表示方法
        i@target_datetime : データを表示する日時 None の場合は当日
        """

        _analysis.create_html(
            self.db_dir_path,
            self.db_data_tbl_name,
            self.db_data_tbl_name_item_list,
            self.html_file_path,
            self.rest_time_name,
            type=type_str,
            target_datetime=target_datetime,
        )

        return


    @QtCore.Slot()
    def signal_func_stop( self ):

        self.stop()

        return
