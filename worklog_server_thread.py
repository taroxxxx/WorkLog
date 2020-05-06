# -*- coding: utf-8 -*-

"""
.. note::
"""

import SimpleXMLRPCServer

from PySide import QtCore


class ServerThread( QtCore.QThread ):

    def __init__( self, ip_address, port_no, server_instance, parent=None  ):
        super( ServerThread, self ).__init__( parent )

        """
        # SimpleXMLRPCServer Thread

        s@ip_address :
        i@port_no :
        @server_instance :
        """

        #self.main_cls = main_cls
        self.ip_address = ip_address
        self.port_no = port_no
        self.server_instance = server_instance


    def run( self ):

        """
        # SimpleXMLRPCServer の開始
        """

        # disable Address already in use
        SimpleXMLRPCServer.SimpleXMLRPCServer.allow_reuse_address=True

        self.xmlrpc_server = SimpleXMLRPCServer.SimpleXMLRPCServer( ( self.ip_address, self.port_no ),
            logRequests=False )

        # register instance
        self.xmlrpc_server.register_instance( self.server_instance )

        try:
            self.xmlrpc_server.serve_forever()

        except:
            pass #self.main_cls.main_logger.debug( u'Except SimpleXMLRPCServer' )

        finally:
            self.quit()


    def stop( self ):

        """
        # SimpleXMLRPCServer の停止
        """

        while self.isRunning():
            self.xmlrpc_server.server_close()

        return 1
