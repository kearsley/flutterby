import pygtk
from gtk import *

import flutterby_db as db

class PCheckButton( CheckButton ):
    def __init__( self, key, label = None, use_underline = True ):
        super( PCheckButton, self ).__init__( label, use_underline )
        
        self.db_key = key

class PComboBox( ComboBox ):
    def __init__( self, key, data_column = 1, model = None ):
        super( PComboBox, self ).__init__( model )
        
        self.db_key = key
        self.data_column = data_column

        self.connect( 'changed', self.save_value )

    def save_value( self, widget ):
        model = self.get_model()
        row = self.get_active_iter()
        value = model.get_value( row, self.data_column )

        print value

        db.set_param( self.db_key, value )

    def restore_value( self ):
        model = self.get_model()
        row = model.get_iter_first()

        while row:
            value = model.get_value( row, self.data_column )
            if value == db.get_param( self.db_key ):
                break
            row = model.iter_next( row )
        if not row:
            return

        self.set_active_iter( row )
        

class PComboBoxText( PComboBox ):
    def __init__( self, key, data_column = 1, model = None ):
        super( PComboBoxText, self ).__init__( key, data_column, model )
        
        self.cell = CellRendererText()
        self.pack_start( self.cell )
        self.add_attribute( self.cell, 'text', 0 )

class LabelItem( HBox ):
    def __init__( self, child, label = None, homogenous = False, spacing = 0 ):
        super( LabelItem, self ).__init__( homogenous, spacing )

        if label:
            self.label = Label( label + ':' )
        else:
            self.label = Label( '' )
        self.label.show()
            
        self.pack_start( self.label, False, False, 0 )
        self.pack_start( child, False, False, 0 )

class DBTreeView( TreeView ):
    def __init__( self, table, columns ):
        self.db_model = ListStore( *[ x[1] for x in columns ] )
        self.table = table
        self.columns = [ x[0] for x in columns ]
        self.refresh_model()
        
        super( DBTreeView, self ).__init__( self.db_model )

        for count in xrange( len( columns ) ):
            cell = CellRendererText()
            if len( columns[ count ] ) < 2 or not columns[ count ][2]:
                column = TreeViewColumn( None, cell, text = 0 )
            else:
                column = TreeViewColumn( columns[ count ][2], cell, text = 0 )
            self.append_column( column )

        self.rows = count

    def refresh_model( self ):
        data = db.execute_sql( 'select %s from %s' % ( ','.join( self.columns ),
                                                       self.table ) )

        self.db_model.clear()
        for row in data:
            self.db_model.append( row )

def prompt_dialog( message, label ):
    def responseToDialog(entry, dialog, response):
        dialog.response(response)
        
    dialog = MessageDialog( None,
                            DIALOG_MODAL | DIALOG_DESTROY_WITH_PARENT,
                            MESSAGE_QUESTION,
                            BUTTONS_OK,
                            None )
    dialog.set_markup( message )
    
    entry = Entry() 
    entry.connect( "activate", responseToDialog, dialog, RESPONSE_OK )

    hbox = HBox()
    hbox.pack_start( Label( label ), False, 5, 5 )
    hbox.pack_end( entry )

    dialog.vbox.pack_end( hbox, True, True, 0 )

    dialog.show_all()
    dialog.run()

    text = entry.get_text()
    dialog.destroy()

    return text
