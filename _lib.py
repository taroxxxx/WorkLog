# -*- coding: utf-8 -*-

"""
.. note::
"""

import re
import time
import logging
import datetime
import subprocess


def to_unicode( src_text, error_func=logging.error ):

    """
    # unicode に変換

    s@src_text : 変換する text
    error_func : error を送出する func
    """

    ans = ''

    try:
        ans = u'{0}'.format( src_text )

    except UnicodeDecodeError:

        try:
            ans = u'{0}'.format( src_text.decode( 'shift_jis' ) )

        except UnicodeDecodeError:

            try:
                ans = u'{0}'.format( src_text.decode( 'ascii' ) )

            except UnicodeDecodeError:
                ans = src_text

    except:
        error_func( '{0}\n{1}'.foamrt( src_text, traceback.format_exc() ) )

    return ans


def get_elapsed_str( start_time_sec, end_time_sec=None, day_disp=0, tmp='{hour:02d}:{min:02d}:{sec:02d}' ):

    """
    # 開始>終了 までの時間をテキストで返す

    i@start_time_sec : 開始 time
    i@end_time_sec : 終了 time
    i@day_disp : 0 では 経過時間、1 では　経過日数+時間 を表示
    s@tmp : テキストテンプレート
    """

    if end_time_sec == None:

        end_time_sec = time.time()

    elapsed_sec = ( end_time_sec - start_time_sec )
    elapsed_sec = 0.0 if elapsed_sec < 0.0 else elapsed_sec

    d = datetime.timedelta( seconds=elapsed_sec )

    min = d.seconds / ( 60 )

    days_str = '{0}days&'.format( d.days ) if day_disp and elapsed_sec > 60 * 60 * 24 * 1 else '' # over 1 days

    fmt_dict = {
        'hour' :( min / 60 ) if day_disp else 24 * d.days + ( min / 60 ),
        'min' : min % ( 60 ),
        'sec' : d.seconds % ( 60 ),
    }

    return '{0}{1}'.format( days_str, tmp.format( **fmt_dict ) )


def get_datetime_str( time_sec, tmp='{year}-{month:02d}/{day:02d} {hour:02d}:{min:02d}:{sec:02d}' ):

    """
    # 入力時間をテキストで返す

    i@time_sec : time
    s@tmp : テキストテンプレート
    """

    time_sec = 0.0 if time_sec == None or time_sec < 0 else time_sec

    d = datetime.datetime.fromtimestamp( time_sec )

    fmt_dict = {

        'year' : d.year,
        'y' : str( d.year )[2:],
        'month' : d.month,
        'day' : d.day,
        'weekday' : ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()],
        'hour' : d.hour,
        'min' : d.minute,
        'sec' : d.second,
        'microsec' : d.microsecond,

    }

    return tmp.format( **fmt_dict ) if time_sec else '-'*5


def get_week_start_end_datatime( d ):

    """
    # d が含まれる週の開始(月)-終了(日)の datetime を返す

    @d : datetime
    """

    week_start_d = d + datetime.timedelta( days=range(0,-7,-1)[ d.weekday() ] ) # to mon
    week_end_d = d + datetime.timedelta( days=range(6,-1,-1)[ d.weekday() ] ) # to sun

    return week_start_d, week_end_d


def get_month_start_end_datatime( y, m ):

    """
    # y,m で指定した月の開始日-終了日の datetime を返す

    i@y : 年
    i@m : 月
    """

    month_start_d = datetime.datetime( y, m, 1, 0,0,0 )

    month_end_d = datetime.datetime( ( y if m!=12 else y+1 ), ( m+1 if m!=12 else 1 ), 1, 0,0,0 )
    month_end_d += datetime.timedelta( days=-1 ) # to previous month-last day

    return month_start_d, month_end_d


"""
def get_logintime():

    date_fmt = re.compile( r'(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)' )
    time_fmt = re.compile( r'(?P<hour>[\d]+):(?P<minute>[\d]+)' )

    year = None
    month = None
    day = None
    hour = None
    minute = None

    sub_proc = subprocess.Popen(
        'quser',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )

    ( stdout, stdin ) = ( sub_proc.stdout, sub_proc.stdin )

    while 1:

        line = stdout.readline()

        data_search = date_fmt.search( line )
        if data_search != None:
            year = int( data_search.group( 'year' ) )
            month = int( data_search.group( 'month' ) )
            day = int( data_search.group( 'day' ) )

        time_search = time_fmt.search( line )
        if time_search != None:
            hour = int( time_search.group( 'hour' ) )
            minute = int( time_search.group( 'minute' ) )

        if not line:
            break

    login_time = time.mktime( datetime.datetime( year,month,day,hour,minute, 0 ).timetuple() )

    return login_time
"""
