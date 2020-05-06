# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import platform


def main( target, target_exe_dir ):

    """
    # pyinstaller 後処理、.exe の移動 & 一時ファイルの削除

    s@target : .exe 名
    s@target_exe_dir : 書き出し先
    """

    if not os.path.isdir( target_exe_dir ):
        sys.stdout.write( 'not found dir: %s' % target_exe_dir )
        sys.exit(1)

    dst_app_dir_path = os.path.join( os.getcwd(), target )

    if os.path.isdir( dst_app_dir_path ):
        shutil.rmtree( dst_app_dir_path, ignore_errors=1 )
        sys.stdout.write( 'remove : {0}\n'.format( dst_app_dir_path ) )

    shutil.copytree( target_exe_dir, dst_app_dir_path )
    sys.stdout.write( '>>> {0}\n'.format( dst_app_dir_path ) )

    for dirname in [ 'build', 'dist', 'zipLib' ]:

        rm_dir_path = os.path.join( os.getcwd(), dirname )

        shutil.rmtree( rm_dir_path, ignore_errors=1 )
        sys.stdout.write( 'remove : {0}\n'.format( rm_dir_path ) )

if __name__ == '__main__':
    main( sys.argv[1], sys.argv[2] )
