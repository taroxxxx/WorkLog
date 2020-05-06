# -*- coding: utf-8 -*-

"""
.. note::
"""

import os
import re
import copy
import time
import psutil
import logging
import datetime
import traceback

import sqlite3

import win32ui
import win32api
import win32gui
import win32process

from PySide import QtCore


import _lib
import _sqlite


class Signal( QtCore.QObject ):

    main_show_away_dialog_signal = QtCore.Signal()
    main_show_workstate_dialog_signal = QtCore.Signal()
    main_set_db_file_path_signal = QtCore.Signal( str )
    main_set_current_project_signal = QtCore.Signal( str )
    main_set_active_project_list_signal = QtCore.Signal( list )

    calendar_set_cur_year_month_signal = QtCore.Signal( int, int )
    calendar_set_has_data_date_item_list_signal = QtCore.Signal( list )


class MainThread( QtCore.QThread ):

    def __init__( self,
        db_dir_path, db_basename_temp,
        is_away_min, interval_sec,
        db_data_tbl_name,
        pri_file_path_fmt, sec_file_path_fmt_list,
        file_name_fmt,
        ignore_drive_list,
        rest_time_name, leave_seat_name, other_project_name
    ):
        super( MainThread, self ).__init__()

        # Signal
        self.signal = Signal()

        ### SETTINGS ###
        self.ignore_drive_list = ignore_drive_list

        self.pri_file_path_fmt = pri_file_path_fmt
        self.sec_file_path_fmt_list = sec_file_path_fmt_list
        self.file_name_fmt = file_name_fmt

        self.running = 1

        self.wait = 0
        self.away_dlg_item = None

        self.db_dir_path = db_dir_path
        self.db_basename_temp = db_basename_temp

        self.is_away_min = is_away_min
        self.interval_sec = interval_sec

        self.cur_year = None
        self.cur_month = None

        self.db_file_path = None
        self.db_data_tbl_name = db_data_tbl_name

        self.rest_time_name = rest_time_name
        self.leave_seat_name = leave_seat_name
        self.other_project_name = other_project_name

        self.prev_project = None

        self.active_project_list = []
        self.is_init_loop = 1


    def set_wait( self, v ):

        self.wait = v
        return


    def set_away_dlg_item( self, item ):

        self.away_dlg_item = item
        return


    def set_workstate( self, workstate ):

        self.workstate = workstate
        return


    def set_prev_project( self, item ):

        self.prev_project = item
        return


    def get_cur_year_month( self ):

        return self.cur_year, self.cur_month


    def run( self ):

        def get_cursor_pos( prev_cursor_pos=( 0, 0 ) ):

            is_logout = 0
            cursor_pos = prev_cursor_pos

            try:
                cursor_pos = win32api.GetCursorPos()

            except Exception as except_inst:

                err_msg = str( except_inst ).decode( 'shift_jis' )

                errno_format = re.compile( "\((?P<no>\d+), 'GetCursorPos', " )
                errno_search = errno_format.search( err_msg )

                errno = None

                if errno_search != None:

                    errno = int( errno_search.group( 'no' ) )

                    if errno == 5: # アクセスが拒否されました。

                        logging.info( 'WELL-KNOWN-ERROR - [Errno {0}] access denied.'.format( errno ) )
                        is_logout = 1

                    else:
                        errno = None

                if errno == None:

                    logging.error( err_msg )
                    logging.error( traceback.format_exc() )

            finally:

                return is_logout, cursor_pos


        def update_db_file_path():

            """
            # 当月の .sqlite の path ＆ Calendar の期間を更新
            """

            d = datetime.datetime.fromtimestamp( time.time() )

            self.cur_year = d.year
            self.cur_month = d.month

            self.db_file_path = os.path.join(
                self.db_dir_path, self.db_basename_temp.format( self.cur_year, self.cur_month )
            )

            self.signal.main_set_db_file_path_signal.emit( self.db_file_path )

            self.signal.calendar_set_cur_year_month_signal.emit( self.cur_year, self.cur_month )

            # 全ての .sqlite から DATA がある DATE を取得、calendar の min-max の指定
            self.signal.calendar_set_has_data_date_item_list_signal.emit(
                _sqlite.db_get_has_data_date_item_list( self.db_dir_path )
            )

            return 1

        def get_cur_window_data( prev_exe, prev_file, prev_project ):

            """
            # Window たタイトルバーから情報を取得

            s@prev_exe :
            s@prev_file :
            s@prev_project :
            """

            cur_exe = '' #cur_exe = prev_exe
            cur_file = '' #cur_file = prev_file
            cur_project = prev_project

            # exe
            try:

                pid = win32process.GetWindowThreadProcessId( win32gui.GetForegroundWindow() ) #This produces a list of PIDs active window relates to
                cur_exe = psutil.Process( pid[-1] ).name() #pid[-1] is the most likely to survive last longer
                # psutil.Process( pid[-1] ).exe() # get absolute path

            except Exception as except_inst:

                err_msg = str( except_inst ).decode( 'shift_jis' )

                logging.error( err_msg )
                logging.error( traceback.format_exc() )


            # window_text
            window_text = ''

            try:
                window_text = win32ui.GetForegroundWindow().GetWindowText()

            except Exception as except_inst:

                err_msg = str( except_inst ).decode( 'shift_jis' )

                if err_msg == 'No window is is in the foreground.': # = desktop
                    pass
                else:
                    logging.error( err_msg )
                    logging.error( traceback.format_exc() )

            window_text = re.sub( r'\\', r'/', window_text )

            # get project
            file_path_search = self.pri_file_path_fmt.search( window_text )

            if file_path_search != None: # primary

                drive = file_path_search.group( 'drive' )

                if not drive in self.ignore_drive_list:
                    cur_project = file_path_search.group( 'project' )

                    if not cur_project in self.active_project_list:
                        self.active_project_list.append( cur_project )

            #print cur_project
            if cur_project == prev_project: # secondary

                for file_path_fmt in self.sec_file_path_fmt_list:

                    file_path_search = file_path_fmt.search( window_text )

                    if file_path_search != None:
                        cur_project = file_path_search.group( 'project' )
                        break # 優先度の高いものから取得

            # file name
            file_name_search = self.file_name_fmt.search( window_text )

            if file_name_search != None:

                ext = file_name_search.group( 'ext' )
                cur_file = file_name_search.group( 'filename' )
                cur_file = '{0}.{1}'.format( cur_file, ext )

            #print window_text
            #print 'prj={0}, exe={1}, file={2}'.format( cur_project, cur_exe, cur_file )

            self.signal.main_set_current_project_signal.emit( cur_project )

            return cur_exe, cur_file, cur_project


        def update_latest_dateend_data( date_end_time=None ):

            """
            # 最後のデータの DATE_END を修正

            @date_end_time : datetime
            """

            # 初回 loop ではは前回ログイン時のデータになるので更新しない
            if self.is_init_loop:
                self.is_init_loop = 0
                return 0

            # update last data's DATA
            sql_connect = sqlite3.connect( self.db_file_path )
            sql_cursor = sql_connect.cursor()

            sql_cursor.execute( 'SELECT MAX( ID ) FROM {0};'.format( self.db_data_tbl_name ) )
            fetchone = sql_cursor.fetchone()

            if fetchone[0] != None:

                max_id = fetchone[0]

                sql_cursor.execute( 'SELECT DATE_END FROM {0} WHERE ID={1};'.format( self.db_data_tbl_name, max_id ) )
                prev_data_end = sql_cursor.fetchone()[0]

                date_end_time = time.time() if date_end_time==None else date_end_time

                # 日付が変わったか確認
                prev_d = datetime.datetime.fromtimestamp( prev_data_end )
                prev_data_day_end_time = time.mktime( datetime.datetime(
                    prev_d.year, prev_d.month, prev_d.day, 23,59,59
                ).timetuple() )

                if prev_data_day_end_time < date_end_time:
                    return 0

                sql_cursor.execute(
                    'UPDATE {0} SET DATE_END={1} WHERE ID={2};'.format( self.db_data_tbl_name, date_end_time, max_id )
                )

                sql_connect.commit()
                sql_connect.close()

            return 1

        def ___main___():
            pass

        try:

            do_initialize = 1

            update_db_file_path() # 当月の .sqlite 取得

            _sqlite.db_set_sqlite_file_path( self.db_file_path, self.db_data_tbl_name )

            cur_exe = ''
            cur_file = ''
            cur_project = ''

            # check work state
            self.wait = 1
            self.signal.main_show_workstate_dialog_signal.emit()

            while self.wait:
                pass

            while self.running:

                d = datetime.datetime.fromtimestamp( time.time() )

                if self.cur_year != d.year or self.cur_month != d.month: # 実行中に 月 が変わったら .sqlite を更新

                    do_initialize = 1
                    update_db_file_path()

                if do_initialize: # initialize value

                    prev_exe = ''
                    prev_file = ''
                    self.prev_project = _sqlite.get_latest_project_data(
                        self.db_file_path,
                        self.other_project_name,
                        [ self.rest_time_name, self.other_project_name ]
                    )

                    self.signal.main_set_current_project_signal.emit( self.prev_project )

                    if not self.prev_project in self.active_project_list:
                        self.active_project_list.append( self.prev_project )

                    is_logout, prev_cursor_pos = get_cursor_pos()

                    is_away = 0
                    away_start_time = time.time()

                    do_wait_loop = 1

                    do_initialize = 0

                if not is_away:

                    cur_exe, cur_file, cur_project = get_cur_window_data( prev_exe, prev_file, self.prev_project )

                    updated = update_latest_dateend_data()

                    if cur_exe != prev_exe or cur_file != prev_file or cur_project != self.prev_project or not updated:

                        tbl_data_list = [
                            ( 'PROJECT', cur_project ),
                            ( 'EXE', cur_exe ),
                            ( 'FILE', cur_file ),
                            ( 'DATE_START', time.time() ),
                            ( 'DATE_END', time.time() ),
                            ( 'WORKSTATE', self.workstate ),
                        ]
                        _sqlite.db_insert_data( self.db_file_path, self.db_data_tbl_name, tbl_data_list )

                    prev_exe = cur_exe
                    prev_file = cur_file
                    self.prev_project = cur_project

                # check mouse cursor move
                is_logout, cur_cursor_pos = get_cursor_pos( prev_cursor_pos=prev_cursor_pos )

                do_wait_loop = 1

                if cur_cursor_pos == prev_cursor_pos:

                    is_away = 1

                    elapsed_sec = time.time() - away_start_time

                    if is_logout or ( elapsed_sec > 60.0 * self.is_away_min ): # over n min

                        self.wait = 1
                        self.signal.main_set_active_project_list_signal.emit( self.active_project_list )
                        self.signal.main_show_away_dialog_signal.emit()

                        while self.wait:
                            pass

                        # Rest Time 以外の時は project を設定
                        is_rest = ( self.away_dlg_item == self.rest_time_name )

                        # 前の DATA を 離席時間の直前に
                        updated = update_latest_dateend_data( date_end_time=away_start_time )

                        if updated:

                            tbl_data_list = [
                                ( 'PROJECT', self.away_dlg_item ),
                                ( 'EXE', self.away_dlg_item if is_rest else self.leave_seat_name ),
                                ( 'FILE', self.away_dlg_item if is_rest else self.leave_seat_name ),
                                ( 'DATE_START', away_start_time ),
                                ( 'DATE_END', time.time() ),
                                ( 'WORKSTATE', self.workstate ),
                            ]
                            _sqlite.db_insert_data( self.db_file_path, self.db_data_tbl_name, tbl_data_list )

                        else:

                            # 日付が変わったら、データを分割
                            cur_d = datetime.datetime.fromtimestamp( time.time() )

                            today_start = time.mktime( datetime.datetime(
                                cur_d.year, cur_d.month, cur_d.day, 0,0,0
                            ).timetuple() )

                            prev_day_end = today_start - 1 # sec

                            tbl_data_list = [
                                ( 'PROJECT', self.away_dlg_item ),
                                ( 'EXE', self.away_dlg_item if is_rest else self.leave_seat_name ),
                                ( 'FILE', self.away_dlg_item if is_rest else self.leave_seat_name ),
                                ( 'DATE_START', away_start_time ),
                                ( 'DATE_END', prev_day_end ),
                                ( 'WORKSTATE', self.workstate ),
                            ]
                            _sqlite.db_insert_data( self.db_file_path, self.db_data_tbl_name, tbl_data_list )

                            tbl_data_list = [
                                ( 'PROJECT', self.away_dlg_item ),
                                ( 'EXE', self.away_dlg_item if is_rest else self.leave_seat_name ),
                                ( 'FILE', self.away_dlg_item if is_rest else self.leave_seat_name ),
                                ( 'DATE_START', today_start ),
                                ( 'DATE_END', time.time() ),
                                ( 'WORKSTATE', self.workstate ),
                            ]
                            _sqlite.db_insert_data( self.db_file_path, self.db_data_tbl_name, tbl_data_list )

                        if not is_rest:
                            self.prev_project = self.away_dlg_item # update project selected on dialog

                        is_away = 0
                        do_wait_loop = 0

                else:

                    is_away = 0
                    away_start_time = time.time() # reset

                    prev_cursor_pos = cur_cursor_pos

                # wait loop
                if do_wait_loop:

                    update_interval = 10*20 # 0.1sec x10 x10 = 20 sec

                    for i in xrange( 10 * self.interval_sec ): # 0.1sec x10 xN = N sec

                        if i%update_interval == ( update_interval-1 ): # check

                            tmp_cur_exe, tmp_cur_file, tmp_cur_project = get_cur_window_data(
                                prev_exe, prev_file, self.prev_project
                            )

                            updated = update_latest_dateend_data()

                            if cur_project != tmp_cur_project or not updated: # check project

                                tbl_data_list = [
                                    ( 'PROJECT', tmp_cur_project ),
                                    ( 'EXE', tmp_cur_exe ),
                                    ( 'FILE', tmp_cur_file ),
                                    ( 'DATE_START', time.time() ),
                                    ( 'DATE_END', time.time() ),
                                    ( 'WORKSTATE', self.workstate ),
                                ]
                                _sqlite.db_insert_data( self.db_file_path, self.db_data_tbl_name, tbl_data_list )

                                cur_exe = tmp_cur_exe
                                cur_file = tmp_cur_file
                                cur_project = tmp_cur_project

                                prev_exe = tmp_cur_exe
                                prev_file = tmp_cur_file
                                self.prev_project = tmp_cur_project

                        if not self.running:
                            break

                        self.msleep( 100 ) # msec = 0.001sec x100 = 0.1sec

                #print cur_project

            # quit thread
            self.quit()

        except:

            logging.error( traceback.format_exc() )


    def stop( self ):

        self.running = 0
        return
