# -*- coding: utf-8 -*-

"""
.. note::
"""

import os
import glob
import time
import logging
import datetime
import traceback

import sqlite3

import _lib


def get_sqlite_tbl_name():

    """
    # table name
    """

    return 'WORKLOG'


def get_sqlite_tbl_name_item_list():

    """
    # sqlite table 設定
    """

    return [

        ( 'ID', 'INTEGER PRIMARY KEY AUTOINCREMENT' ), # auto

        ( 'PROJECT', 'TEXT DEFAULT ""' ),
        ( 'EXE', 'TEXT DEFAULT ""' ),
        ( 'FILE', 'TEXT DEFAULT ""' ),

        ( 'DATE_START', 'INTEGER DEFAULT -1' ),
        ( 'DATE_END', 'INTEGER DEFAULT -1' ),

        ( 'WORKSTATE', 'INTEGER DEFAULT -1' ), # self.workstate_item_list.index( selection )

    ]


def db_connect_db(
    sqlite_file_path
):
    """
    # sqlite_file_path の connect を返します
    s@sqlite_file_path : .sqlite
    """

    sql_connect = None

    try:
        sql_connect = sqlite3.connect( sqlite_file_path )

    except:
        logging.error( traceback.format_exc() )

    return sql_connect


def db_execute_sql_cmd_args(
    sqlite_file_path,
    sql_cmd_args,
    text_factory=sqlite3.OptimizedUnicode
):
    """
    # sqlite_file_path の connect を返します
    s@sqlite_file_path : .sqlite

    s[]@sql_cmd_args :
    create table [
        'CREATE TABLE IF NOT EXISTS WORKLOG (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            PROJECT TEXT DEFAULT "",
            EXE TEXT DEFAULT "",
            FILE TEXT DEFAULT "",
            DATE_START INTEGER DEFAULT -1,
            DATE_END INTEGER DEFAULT -1,
            WORKSTATE INTEGER DEFAULT -1
        );
    ],

    insert data [
        'INSERT INTO WORKLOG ( PROJECT, EXE, FILE, DATE_START, DATE_END, WORKSTATE ) VALUES ( ?, ?, ?, ?, ?, ? );',
        [u'Development', 'python.exe', '', f@time, f@time, 1]
    ]
    text_factory : sql_connect.text_factory
    """

    sql_connect = db_connect_db( sqlite_file_path )
    sql_connect.text_factory = text_factory

    result = 0

    try:
        sql_connect.execute( *sql_cmd_args )
        sql_connect.commit()
        result = 1

    except sqlite3.OperationalError:
        logging.warning( traceback.format_exc() )
        logging.warning( sql_cmd_args )

    except:
        logging.error( traceback.format_exc() )

    finally:
        if sql_connect != None:
            sql_connect.close()

    return result


def db_insert_data(
    sqlite_file_path,
    tbl_name,
    tbl_data_list
):
    """
    # tbl_data_list を tbl_name に INSERT
    s@sqlite_file_path : .sqlite
    s@tbl_name :
    s[]@tbl_data_list : [ [ data_name, value ], ... ]
    """

    if sqlite_file_path == None:

        return 0

    col_list = [ data[0] for data in tbl_data_list ]
    col_str = ', '.join( col_list )

    val_tmp_list = [ '?' for data in tbl_data_list ]
    val_tmp_str = ', '.join( val_tmp_list )

    sql_cmd_tmp = 'INSERT INTO {0} ( {1} ) VALUES ( {2} );'.format( tbl_name, col_str, val_tmp_str )

    return db_execute_sql_cmd_args( sqlite_file_path, [ sql_cmd_tmp, [ data[1] for data in tbl_data_list ] ] )


def db_set_sqlite_file_path(
    sqlite_file_path,
    tbl_name,
):
    """
    # .sqlite の初期設定
    s@sqlite_file_path : .sqlite
    s@tbl_name :

    s[]@tbl_data_list : [ [ data_name, value ], ... ] # nouse?

    """

    if sqlite_file_path != None:

        sqlite_dir_path = os.path.dirname( sqlite_file_path )

        if not os.path.isdir( sqlite_dir_path ):
            os.makedirs( sqlite_dir_path )

        sqlite_tbl_name_item_list = get_sqlite_tbl_name_item_list()

        sql_cmd_line_list = []

        for tbl_name_item in sqlite_tbl_name_item_list:
            sql_cmd_line_list.append( ' '.join( tbl_name_item ) )

        sql_cmd = '''\
CREATE TABLE IF NOT EXISTS {0} (
{1}
);
'''
        sql_cmd = sql_cmd.format( tbl_name, ',\n'.join( sql_cmd_line_list ) )

        # create table
        db_execute_sql_cmd_args( sqlite_file_path, [ sql_cmd ] )

        fetchall = db_fetchall(
            sqlite_file_path, "pragma table_info({0});".format( tbl_name )
        )

        cur_table_item_name_list = []
        for item in fetchall:
            cur_table_item_name_list.append( item[1] )

        for tbl_name_item in sqlite_tbl_name_item_list:

            if not tbl_name_item[0] in cur_table_item_name_list:

                sql_cmd = 'ALTER TABLE {0} ADD {1};'.format( tbl_name, ' '.join( tbl_name_item ) )
                logging.info( 'ALTER TABLE : {0}'.format( sql_cmd ) )

                db_execute_sql_cmd_args( sqlite_file_path, [ sql_cmd ] )

    return 1


def db_fetchall(
    sqlite_file_path,
    cmd
):
    """
    # cmd を実行して fetchall 結果を返す
    s@sqlite_file_path : .sqlite
    s@cmd :sql cmd
    """

    sql_connect = db_connect_db( sqlite_file_path )
    sql_cursor = sql_connect.cursor()

    sql_cursor.execute( cmd )

    return sql_cursor.fetchall()


def db_fetchall_multiple(
    sqlite_dir_path,
    cmd
):
    """
    # sqlite_dir_path 以下の全ての .sqlite に cmd を実行して fetchall 結果をまとめて返す
    s@sqlite_dir_path : path
    s@cmd :sql cmd
    """

    date_list = []

    sqlite_file_path_list = glob.glob( os.path.join( sqlite_dir_path, r'*.sqlite' ) )

    for sqlite_file_path in sqlite_file_path_list:
        date_list.extend( db_fetchall( sqlite_file_path, cmd ) )

    return date_list


def db_get_target_day_data(
    sqlite_dir_path,
    sqlite_tbl_name,
    year,
    month,
    day
):
    """
    # sqlite_dir_path 以下の全ての .sqlite から指定した日時の fetchall 結果をまとめて返す
    s@sqlite_dir_path : path
    s@sqlite_tbl_name :
    i@year :
    i@month :
    i@day :
    """

    time_today_start = time.mktime( datetime.datetime( year, month, day, 0,0,0 ).timetuple() )
    time_today_end = time.mktime( datetime.datetime( year, month, day, 23,59,59 ).timetuple() )

    cmd = 'SELECT * FROM {0} WHERE {1} <= DATE_START AND DATE_END <= {2};'.format(
        sqlite_tbl_name, time_today_start, time_today_end
    )
    return db_fetchall_multiple( sqlite_dir_path, cmd )


def db_get_target_week_data(
    sqlite_dir_path,
    sqlite_tbl_name,
    year,
    month,
    day
):
    """
    # sqlite_dir_path 以下の全ての .sqlite から指定した日時が含まれる週の fetchall 結果をまとめて返す
    s@sqlite_dir_path : path
    s@sqlite_tbl_name :
    i@year :
    i@month :
    i@day :
    """

    d = datetime.datetime( year, month, day, 0,0,0 )

    week_start_d, week_end_d = _lib.get_week_start_end_datatime( d )

    time_today_start = time.mktime( datetime.datetime(
        week_start_d.year, week_start_d.month, week_start_d.day, 0,0,0
    ).timetuple() )

    time_today_end = time.mktime( datetime.datetime(
        week_end_d.year, week_end_d.month, week_end_d.day, 23,59,59
    ).timetuple() )

    cmd = 'SELECT * FROM {0} WHERE {1} <= DATE_START AND DATE_END <= {2};'.format(
        sqlite_tbl_name, time_today_start, time_today_end
    )
    return db_fetchall_multiple( sqlite_dir_path, cmd )


def db_get_target_month_data(
    sqlite_dir_path,
    sqlite_tbl_name,
    year,
    month
):
    """
    # sqlite_dir_path 以下の全ての .sqlite から指定した月の fetchall 結果をまとめて返す
    s@sqlite_dir_path : path
    s@sqlite_tbl_name :
    i@year :
    i@month :
    """

    start_d, end_d = _lib.get_month_start_end_datatime( year, month )

    time_today_start = time.mktime( datetime.datetime(
        start_d.year, start_d.month, start_d.day, 0,0,0
    ).timetuple() )

    time_today_end = time.mktime( datetime.datetime(
        end_d.year, end_d.month, end_d.day, 23,59,59
    ).timetuple() )

    cmd = 'SELECT * FROM {0} WHERE {1} <= DATE_START AND DATE_END <= {2};'.format(
        sqlite_tbl_name, time_today_start, time_today_end
    )
    return db_fetchall_multiple( sqlite_dir_path, cmd )


def db_get_has_data_date_item_list(
    sqlite_dir_path,
):
    """
    # sqlite_dir_path 以下の全ての .sqlite から data がある日付のリスト [ [ d.year, d.month, d.day ], ... ] を返す

    s@sqlite_dir_path : path
    """

    sqlite_tbl_name = get_sqlite_tbl_name()

    date_list = []
    cmd = 'SELECT DATE_START FROM {0};'.format( sqlite_tbl_name )

    sqlite_file_path_list = glob.glob( os.path.join( sqlite_dir_path, r'*.sqlite' ) )

    for sqlite_file_path in sqlite_file_path_list:

        try:

            data_item_list = db_fetchall( sqlite_file_path, cmd )

            for data_item in data_item_list:

                d = datetime.datetime.fromtimestamp( data_item[0] )

                date_item = [ d.year, d.month, d.day ]

                if not date_item in date_list:
                    date_list.append( date_item )

        except sqlite3.OperationalError:
            logging.info( 'No Table'.format( sqlite_file_path ) )
        except:
            logging.error( traceback.format_exc() )

    return date_list


def get_latest_project_data(
    sqlite_file_path,
    init_prj,
    ignore_prj_list
):

    """
    # sqlite_file_path から 最新の PROJECT を取得

    s@sqlite_file_path : path
    s@init_prj : 初期設定
    s[]@ignore_prj_list : 除外する list
    """

    sqlite_tbl_name = get_sqlite_tbl_name()

    # update last data's DATA
    sql_connect = sqlite3.connect( sqlite_file_path )
    sql_cursor = sql_connect.cursor()

    sql_cursor.execute( 'SELECT MAX( ID ) FROM {0};'.format( sqlite_tbl_name ) )

    latest_project = init_prj
    fetchone = sql_cursor.fetchone()

    if fetchone[0] != None:

        max_id = int( fetchone[0] )

        count = 0
        while count<100 and 0<max_id:

            sql_cursor.execute( 'SELECT PROJECT FROM {0} WHERE ID={1};'.format( sqlite_tbl_name, max_id ) )
            latest_project = sql_cursor.fetchone()[0]

            if not latest_project in ignore_prj_list: # ignore Rest
                break

            max_id -= 1
            count += 1

    return latest_project


def get_lecent_project_list(
    sqlite_dir_path,
    ignore_prj_list,
):

    """
    # sqlite_file_path から 最新の PROJECT を取得

    s@sqlite_dir_path : path
    s@sqlite_tbl_name : 初期設定
    s[]@ignore_prj_list : 除外する list
    """

    sqlite_tbl_name = get_sqlite_tbl_name()

    sqlite_file_path_list = glob.glob( os.path.join( sqlite_dir_path, r'*.sqlite' ) )
    sqlite_file_path_list = sorted( sqlite_file_path_list, reverse=1 )[:2] # 直近二ヶ月

    prj_item_list = []

    for sqlite_file_path in sqlite_file_path_list:

        prj_data_list = db_fetchall( sqlite_file_path, 'SELECT PROJECT FROM {0};'.format( sqlite_tbl_name ) )
        prj_item_list.extend(
            [ prj_data[0] for prj_data in prj_data_list if ( not prj_data[0] in ignore_prj_list ) and len( prj_data[0] ) ]
        )

    prj_item_list = [ item for item in set( prj_item_list ) ]

    return prj_item_list
