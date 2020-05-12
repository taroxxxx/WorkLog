# -*- coding: utf-8 -*-

"""
.. note::
"""

import os
import re
import time
import codecs
import datetime

from operator import itemgetter

import _lib
import _sqlite


def create_html(
    db_dir_path,
    db_data_tbl_name,
    db_data_tbl_name_item_list,
    html_file_path,
    rest_time_name,
    type='today',
    target_datetime=None,
):

    """
    # .html の作成

    s@db_dir_path : sqlite を保存しているディレクトリ
    s@db_data_tbl_name : sqlite table name
    s[]@db_data_tbl_name_item_list : sqlite のデータリスト
    s@html_file_path : html path
    s@type='today' : 表示方法
    i@target_datetime=None : データを表示する日時 None の場合は当日
    """

    db_data_tbl_name_index_list = [ item[0] for item in db_data_tbl_name_item_list ]

    def get_item_str(
        db_item,
        data_name,
        no_data_str='',
        do_splitext=0,
        remove_ver=0,
    ):

        """
        # db_item から指定したデータ名を取得

        s[]@db_item : sqlite fetch data
        s@data_name : 取得するデータ名
        s@no_data_str='' : data がなかった場合に使用する str
        i@do_splitext=0 : 1 の場合は .ext を分離
        """

        item_str = db_item[ db_data_tbl_name_index_list.index( data_name ) ]

        if do_splitext:
            item_str, ext = os.path.splitext( item_str )

        if remove_ver: # remove (_t#)_v#
            item_str = re.sub( r'(_t[\d]+)*[_]*v[\d]+[_\w]*', '', item_str )

        return item_str if len( item_str ) else ( no_data_str if len(no_data_str) else item_str )


    def ___get_sqlite_data___():
        pass

    exe_data_name = 'EXE'
    file_data_name = 'FILE'
    prj_data_name = 'PROJECT'

    no_prj_str = 'No Project'

    week_day_list = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    html_dir_path = os.path.dirname( html_file_path )
    if not os.path.isdir( html_dir_path ):
        os.makedirs( html_dir_path )

    d = target_datetime if ( target_datetime != None ) else datetime.datetime.fromtimestamp( time.time() )

    # get database data
    tgt_date_str = ''
    db_item_list = []

    duration_type = 0 # day=0, week=1, month=2

    if type in [ 'today', 'previousday', 'specified_date' ]:

        if type in [ 'today', 'specified_date' ]:

            db_item_list = _sqlite.db_get_target_day_data( db_dir_path, db_data_tbl_name, d.year, d.month, d.day )

        elif type == 'previousday': # データがある日まで戻る

            count = 0

            while not len( db_item_list ) and count<10:

                d -= datetime.timedelta( days=1 )
                db_item_list = _sqlite.db_get_target_day_data( db_dir_path, db_data_tbl_name, d.year, d.month, d.day )

                count += 1

        tgt_date_str = '{0}-{1:02d}/{2:02d}({3})'.format(
            d.year, d.month, d.day, week_day_list[d.weekday()]
        ) if len( db_item_list ) else 'No Previous Day Data'

    elif type in [ 'thisweek', 'previousweek', 'specified_week' ]:

        duration_type = 1

        if type == 'previousweek':

            d -= datetime.timedelta( days=7 )

        db_item_list = _sqlite.db_get_target_week_data( db_dir_path, db_data_tbl_name, d.year, d.month, d.day )

        week_start_d, week_end_d = _lib.get_week_start_end_datatime( d )

        tgt_date_str = '{0}-{1:02d}/{2:02d}({4})~{3:02d}({5})'.format(
            week_start_d.year, week_start_d.month, week_start_d.day, week_end_d.day,
            week_day_list[week_start_d.weekday()], week_day_list[week_end_d.weekday()]
        ) if len( db_item_list ) else 'No Week Data'

    elif type in [ 'month' ]:

        duration_type = 2

        db_item_list = _sqlite.db_get_target_month_data( db_dir_path, db_data_tbl_name, d.year, d.month )

        tgt_date_str = '{0}-{1:02d}'.format(
            d.year, d.month
        ) if len( db_item_list ) else 'No Month Data'

    def ___get_unique_data___():
        pass


    uniquie_exe_list = []
    uniquie_file_list = []
    uniquie_project_list = []

    for index, db_item in enumerate( db_item_list ):

        uniquie_exe_list.append(
            get_item_str( db_item, exe_data_name, do_splitext=1 )
        )

        uniquie_file_list.append(
            get_item_str( db_item, file_data_name, remove_ver=( duration_type!= 0 ) )
        ) # week,mondh の場合は v### を削除

        uniquie_project_list.append(
            get_item_str( db_item, prj_data_name, no_data_str=no_prj_str )
        )

    uniquie_exe_list = sorted( [ item for item in set( uniquie_exe_list ) ] )
    uniquie_file_list = sorted( [ item for item in set( uniquie_file_list ) ] )
    uniquie_project_list = sorted( [ item for item in set( uniquie_project_list ) ] )


    def get_db_items(
        db_item,
        prev_time_end
    ):
        """
        # db_item からデータを取得

        @db_item
        @prev_time_end
        """
        time_start = db_item[ db_data_tbl_name_index_list.index( 'DATE_START' ) ]
        time_end = db_item[ db_data_tbl_name_index_list.index( 'DATE_END' ) ]

        tmp_start_d = datetime.datetime.fromtimestamp( time_start )
        tmp_end_d = datetime.datetime.fromtimestamp( time_end )

        if tmp_start_d.day != tmp_end_d.day: # 日付をまたいでいた場合
            return None, None, None, None, None

        exe_str = get_item_str( db_item, exe_data_name, do_splitext=1 )
        file_str = get_item_str( db_item, file_data_name, remove_ver=( duration_type!= 0 ) )
        project_str = get_item_str( db_item, prj_data_name, no_data_str=no_prj_str )

        if prev_time_end != None and time_start < prev_time_end:
            # 前の data の終了時刻よりも、開始時刻が早い場合は修正
            time_start = prev_time_end

        if time_end < time_start:
            # 終了時刻よりも、開始時刻が早い場合は修正
            time_end = time_start

        return time_start, time_end, exe_str, file_str, project_str


    def append_elapsed_time_to_dict(
        src_elapsed_time_dict,
        src_key,
        elapsed_time
    ):

        """
        # src_key の経過時間を src_elapsed_time_dict[ src_key ] に append、src_key 毎の累計時間を計算

        src_elapsed_time_dict : 対象の dict
        s@src_key : dict key
        i@elapsed_time : 追加する時間
        """

        if len( src_key ) and not src_elapsed_time_dict.has_key( src_key ):
            src_elapsed_time_dict[ src_key ] = []

        if src_elapsed_time_dict.has_key( src_key ):
            src_elapsed_time_dict[ src_key ].append( elapsed_time )

        return src_elapsed_time_dict


    def append_prj_file_time_start_end_to_dict(
        src_time_dict,
        project_str,
        file_str,
        time_start,
        time_end
    ):

        """
        # src_time_dict[ src_key ] = [ [ time_start ... ],[ time_end ...] ]

        src_time_dict : 対象の dict
        s@project_str :
        s@file_str :
        i@time_start :
        i@time_end :
        """

        src_key = '{0};{1}'.format( project_str, file_str )

        if len( src_key ) and not src_time_dict.has_key( src_key ):
            src_time_dict[ src_key ] = [ [], [] ]

        if src_time_dict.has_key( src_key ):
            src_time_dict[ src_key ][0].append( time_start )
            src_time_dict[ src_key ][1].append( time_end )

        return src_time_dict


    def ___get_pichart_data___():
        pass


    work_elapsed_time_list = []
    private_elapsed_time_list = []

    work_rest_elapsed_time_list = []
    private_rest_elapsed_time_list = []

    uniquie_exe_elapsed_time_dict = {}
    uniquie_file_elapsed_time_dict = {}
    uniquie_project_elapsed_time_dict = {}

    uniquie_prj_file_time_start_end_dict = {}

    prev_time_end = None

    for index, db_item in enumerate( db_item_list ):

        time_start, time_end, exe_str, file_str, project_str = get_db_items( db_item, prev_time_end )

        if time_start == None:
            continue

        project = db_item[ db_data_tbl_name_index_list.index( 'PROJECT' ) ]
        is_rest = ( project == rest_time_name )

        is_private = 0
        workstate_index = db_data_tbl_name_index_list.index( 'WORKSTATE' )
        if workstate_index < len( db_item ) : # WORKSTATE 追加以前対応
            workstate = db_item[ workstate_index ]
            is_private = ( workstate==2 )
            # [ 'Office Work', 'Remote Work', 'Private Use' ].index( item )

        elapsed_time = time_end - time_start

        if is_private:
            if is_rest:
                private_rest_elapsed_time_list.append( elapsed_time )
            else:
                private_elapsed_time_list.append( elapsed_time )
        else:
            if is_rest:
                work_rest_elapsed_time_list.append( elapsed_time )
            else:
                work_elapsed_time_list.append( elapsed_time )

        uniquie_exe_elapsed_time_dict = append_elapsed_time_to_dict(
            uniquie_exe_elapsed_time_dict,
            exe_str,
            elapsed_time
        )

        uniquie_file_elapsed_time_dict = append_elapsed_time_to_dict(
            uniquie_file_elapsed_time_dict,
            file_str,
            elapsed_time
        )

        uniquie_project_elapsed_time_dict = append_elapsed_time_to_dict(
            uniquie_project_elapsed_time_dict,
            '{0}{1}'.format( project_str, ' ( private )' if is_private else '' ),
            elapsed_time
        )

        uniquie_prj_file_time_start_end_dict = append_prj_file_time_start_end_to_dict(
            uniquie_prj_file_time_start_end_dict,
            project_str, file_str,
            time_start, time_end,
        )

        prev_time_end = time_end


    def append_timeline_chart_line_list(
        src_list,
        rowlabel,
        name,
        time_start,
        time_end,
        do_merge_previous=1,
    ):

        """
        # src_list に timeline chart 行追加、追加後の src_list を返します

        s[]@src_list : 行を追加するリスト
        s@rowlabel : timeline でのラベル
        s@name : timeline でのデータ名
        i@time_start : timeline での開始日時
        i@time_end : timeline での終了日時
        i@do_merge_previous : 処理が不要な場合に 0、 処理エラーが起きる？？
        """

        if len( name ):

            start_d = datetime.datetime.fromtimestamp( time_start )
            end_d = datetime.datetime.fromtimestamp( time_end )

            fmt_dict = {
                'label' : rowlabel,
                'name' : name,

                'sy' : start_d.year, 'smo' : start_d.month-1, 'sd' : start_d.day,
                'sh' : start_d.hour, 'sm' : start_d.minute, 'ss' :  start_d.second,

                'ey' : end_d.year, 'emo' : end_d.month-1, 'ed' : end_d.day,
                'eh' : end_d.hour, 'em' : end_d.minute, 'es' : end_d.second,
            }

            merge_previous = 0

            if do_merge_previous and len( src_list ):

                format = re.compile( "\['[\(\)\w\s.,-]+','(?P<name>[\w\s.,-]+)+',")
                search = format.search( src_list[-1] )
                #print src_list[-1], search
                if search != None:

                    prev_name = search.group( 'name' ) # get from line
                    merge_previous = (name == prev_name) # 前の行と name が一致

                    format = re.compile(
                        ',new Date\((?P<y>[\d]+),(?P<mo>[\d]+),(?P<d>[\d]+),(?P<h>[\d]+),(?P<mi>[\d]+),(?P<s>[\d]+)\) \]'
                    )
                    search = format.search( src_list[-1] )

                    if search != None:
                        # 経過時間が範囲内＆開始が前の終了を超えていない
                        prev_end_d = datetime.datetime(
                            *[ int( item ) + ( 0 if id != 1 else 1 )for id, item in enumerate( search.groups() ) ]
                        )# time line chart の month は -1
                        merge_previous = min( merge_previous, ( 0.0<=( start_d-prev_end_d ).total_seconds()<120.0 ) )

            if merge_previous:
                # 前の行の end date を更新
                search = re.search( 'new Date\([\d,]+\) ]', src_list[-1])
                if search != None:
                    src_list[-1] = re.sub(
                        re.sub( r'\)', r'\\)', re.sub( r'\(', r'\\(', search.group(0) ) ),
                        'new Date({ey},{emo},{ed},{eh},{em},{es}) ]'.format( **fmt_dict ),
                        src_list[-1]
                    )
            else:
                line_tmp = """      ['{label}','{name}',new Date({sy},{smo},{sd},{sh},{sm},{ss}),"""
                line_tmp += """new Date({ey},{emo},{ed},{eh},{em},{es}) ]"""
                src_list.append( line_tmp.format( **fmt_dict ) )

        return src_list


    def ___get_timeline_data___():
        pass


    exe_tl_data_line_list = []
    file_tl_data_line_list = []
    project_tl_data_line_list = []

    prev_time_end = None
    init_weekday_id = None

    tmp_d = datetime.datetime.fromtimestamp( time.time() )

    for index, db_item in enumerate( db_item_list ):

        time_start, time_end, exe_str, file_str, project_str = get_db_items( db_item, prev_time_end )

        if time_start == None:
            continue

        tmp_time_start = time_start
        tmp_time_end = time_end
        rowlabel_suffix = ''

        if duration_type==1: # week

            # y m d を同じに 曜日毎にラベル
            start_d = datetime.datetime.fromtimestamp( tmp_time_start )

            if init_weekday_id == None:
                init_weekday_id = start_d.weekday()

            weekday = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][ start_d.weekday() ]
            rowlabel_suffix = ' ( {0} )'.format( weekday )

            tmp_time_start = time.mktime( datetime.datetime(
                tmp_d.year, tmp_d.month, tmp_d.day,
                start_d.hour, start_d.minute, start_d.second ).timetuple()
            )

            end_d = datetime.datetime.fromtimestamp( tmp_time_end )
            tmp_time_end = time.mktime( datetime.datetime(
                tmp_d.year, tmp_d.month, tmp_d.day,
                end_d.hour, end_d.minute, end_d.second ).timetuple()
            )

        exe_tl_data_line_list = append_timeline_chart_line_list(
            exe_tl_data_line_list,
            '{0}{1}'.format( '.exe', rowlabel_suffix ),
            exe_str,
            tmp_time_start, tmp_time_end,
        )

        project_tl_data_line_list = append_timeline_chart_line_list(
            project_tl_data_line_list,
            '{0}{1}'.format( '' if duration_type==1 else 'project', rowlabel_suffix ),
            project_str,
            tmp_time_start, tmp_time_end,
        )

        file_tl_data_line_list = append_timeline_chart_line_list(
            file_tl_data_line_list,
            '{0}{1}'.format( 'file', rowlabel_suffix ),
            file_str,
            tmp_time_start, tmp_time_end,
        )

        prev_time_end = time_end

    if duration_type in [ 2 ]: # month 各ファイル毎のタイムラインを作成

        file_tl_data_line_list = []

        prj_file_key_list = uniquie_prj_file_time_start_end_dict.keys()
        prj_file_key_list = sorted( prj_file_key_list )

        for prj_file_key in prj_file_key_list:

            prj_file_key_split = prj_file_key.split( ';' )
            prj_key = prj_file_key_split[0]
            file_key = prj_file_key_split[1]

            if not len( file_key ):
                continue

            sum_elapsed_time = sum( uniquie_file_elapsed_time_dict[ file_key ] )
            sum_elapsed_time_str = _lib.get_elapsed_str( 0.0, sum_elapsed_time, tmp='{hour:02d}:{min:02d}' )

            basename, ext = os.path.splitext( file_key )
            label_str = '{0} ({1})'.format( file_key, sum_elapsed_time_str )
            label_str = _lib.to_unicode( label_str )

            file_tl_data_line_list = append_timeline_chart_line_list(
                file_tl_data_line_list,
                '{0} [{1}]'.format( prj_key, ext ),
                label_str,
                min( uniquie_prj_file_time_start_end_dict[ prj_file_key ][0] ),
                max( uniquie_prj_file_time_start_end_dict[ prj_file_key ][1] ),
                do_merge_previous=0,
            ) # '{0} ({1})'.format( _lib.to_unicode( file_key ), sum_elapsed_time_str ),


    def get_piechart_line_list( src_dict, ignore_time=None ):

        """
        # src_dict の key 毎の累計経過時間の pichart 行を list に追加、 chart_line_list を返します

        src_dict : dict[key] = [ time, time... ]
        """

        chart_line_list = []

        src_key_item_list = [ [ key, sum( src_dict[key] ) ] for key in src_dict.keys() ]
        src_key_item_list = sorted( src_key_item_list, key=itemgetter( 1 ), reverse=1 )

        for src_key in [ item[0] for item in src_key_item_list ]:

            time_sum = sum( src_dict[src_key] )

            if ignore_time != None:
                if time_sum < ignore_time:
                    continue

            chart_line_list.append( """      ['{0} = {1}', {2}]""".format(
                src_key,
                _lib.get_elapsed_str( 0.0, time_sum, tmp='{hour:02d}:{min:02d}' ),
                int( (time_sum/60.0)*100.0 )*0.01
            ) )

        return chart_line_list


    chart_line_exe_list = get_piechart_line_list( uniquie_exe_elapsed_time_dict )

    chart_line_file_list = get_piechart_line_list(
        uniquie_file_elapsed_time_dict
    ) # week,month の場合は 1時間以内のデータを除外 ignore_time=( None if duration_type==0 else (60*60*1) ) # 1h

    chart_line_project_list = get_piechart_line_list( uniquie_project_elapsed_time_dict )


    ##### piechart #####
    def ___piechart_html___():
        pass

    piechart_size = 500
    timeline_height = 400 if duration_type==1 else 300
    timeline_height = 5000 if duration_type==2 else timeline_height
    chart_width = 1500

    html_piechart_line ='''\
<script type="text/javascript">
  google.charts.setOnLoadCallback(drawChart);
  function drawChart() {{
    var data = google.visualization.arrayToDataTable([
      ['itemname', 'minute'],
{data_line}
    ]);
    var options = {{
      title: '- {title} -', pieSliceText: 'label', legend: 'none'
    }};
    var chart = new google.visualization.PieChart(document.getElementById('{chart_name}'));
    chart.draw(data, options);
  }}
</script>
'''

    html_piechart_body_line = '''<span id="{chart_name}" style="display: inline-block;'''
    html_piechart_body_line += ''' width: {width}; height: {height};"></span>'''

    html_piechart_line_list = []
    html_piechart_body_line_list = []

    for item in [
        [ 'project', 'piechart_project', chart_line_project_list ],
        [ '.exe', 'piechart_exe', chart_line_exe_list ],
        [ 'file', 'piechart_file', chart_line_file_list ],
    ]:

        fmt_dict = {
            'title' : item[0],
            'chart_name' : item[1],
            'data_line' : ',\n'.join( item[2] ),
            'width' : piechart_size,
            'height' : piechart_size,
        }

        html_piechart_line_list.append( html_piechart_line.format( **fmt_dict ) )
        html_piechart_body_line_list.append( html_piechart_body_line.format( **fmt_dict ) )


    ##### timeline #####
    def ___timeline_html___():
        pass

    html_timeline_line ='''\
<script type="text/javascript">
  google.charts.setOnLoadCallback(drawChart);
  function drawChart() {{
    var dataTable = new google.visualization.DataTable();
    dataTable.addColumn({{ type: 'string', id: 'RowLabel' }});
    dataTable.addColumn({{ type: 'string', id: 'Name' }});
    dataTable.addColumn({{ type: 'date', id: 'Start' }});
    dataTable.addColumn({{ type: 'date', id: 'End' }});
    dataTable.addRows([
{data_line}
    ]);
    var options = {{
      timeline: {{ colorByRowLabel: false, showBarLabels: true, groupByRowLabel: true }},
      avoidOverlappingGridLines: false,
      colors: [ '#ff9500', '#f62e36', '#b5b5ac', '#009bbf', '#00bb85', '#c1a470', '#8f76d6', '#9c5e31' ]
    }};
    var chart = new google.visualization.Timeline(document.getElementById('{chart_name}'));
    chart.draw(dataTable, options);
  }}
</script>
'''

    html_timeline_body_line ='''<div id="{chart_name}" style="height: {height}px;"></div>'''
    # width: {width}px;

    html_timeline_line_list = []
    html_timeline_body_line_list = []

    merged_data_list = []

    if duration_type==0: # day
        merged_data_list = project_tl_data_line_list + exe_tl_data_line_list + file_tl_data_line_list
    elif duration_type==1: # week
        merged_data_list = project_tl_data_line_list # + file_tl_data_line_list
    elif duration_type==2: # month
        merged_data_list = file_tl_data_line_list

    fmt_dict = {
        'title' : 'timeline',
        'chart_name' : 'timeline',
        'data_line' : ',\n'.join( merged_data_list ),
        'width' : piechart_size*3,
        'height' : timeline_height
    }

    html_timeline_line_list.append( html_timeline_line.format( **fmt_dict ) )
    html_timeline_body_line_list.append( html_timeline_body_line.format( **fmt_dict ) )

    ##### htnl #####
    def ___html___():
        pass

    html_line = '''\
<html>
<title>WorkLog</title>
<head>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">google.charts.load("current", {{packages:["timeline", "corechart"]}});</script>
{piechart_line}
{timeline_line}
</head>
<body>
{info}<br>
{piechart_body_line}
<div>
{timeline_body_line}
</div>
</body>
</html>
'''

    sum_work_elapsed_time = sum( work_elapsed_time_list )
    sum_work_rest_elapsed_time = sum( work_rest_elapsed_time_list )
    sum_private_elapsed_time = sum( private_elapsed_time_list )
    sum_private_rest_elapsed_time = sum( private_rest_elapsed_time_list )

    html_line = html_line.format( **{
        'info' : '{0} : Work = {1} ( Rest = {2} ) | Private Use = {3} ( Rest = {4} ) ({5}data)'.format(
            tgt_date_str,
            _lib.get_elapsed_str( 0.0, sum_work_elapsed_time, tmp='{hour:02d}:{min:02d}' ),
            _lib.get_elapsed_str( 0.0, sum_work_rest_elapsed_time, tmp='{hour:02d}:{min:02d}' ),
            _lib.get_elapsed_str( 0.0, sum_private_elapsed_time, tmp='{hour:02d}:{min:02d}' ),
            _lib.get_elapsed_str( 0.0, sum_private_rest_elapsed_time, tmp='{hour:02d}:{min:02d}' ),
            len( db_item_list )
        ),
        'piechart_line' : ''.join( html_piechart_line_list ) if len( db_item_list ) else '',
        'piechart_body_line' : '\n'.join( html_piechart_body_line_list ) if len( db_item_list ) else '',
        'timeline_line' : ''.join( html_timeline_line_list ) if len( db_item_list ) and ( duration_type!=3 ) else '',
        'timeline_body_line' : ''.join( html_timeline_body_line_list ) if len( db_item_list ) and ( duration_type!=3 ) else '',
    } )

    with codecs.open( html_file_path, 'w', 'utf-8' ) as f:
        f.write( html_line )

    os.startfile( html_file_path )

    return 1
