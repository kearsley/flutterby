import time

import pango, pygtk
from gtk import *

import webbrowser

import flutterby_resources as res
import flutterby_tweets as tweets

from flutterby_functions import *

import flutterby_db as db

class PCheckButton( CheckButton ):
    def __init__( self, key, label = None, use_underline = True ):
        super( PCheckButton, self ).__init__( label, use_underline )
        
        self.db_key = key
        self.set_active( db.get_param( self.db_key, False ) )

        self.connect( 'toggled', self.toggle_event )

    def toggle_event( self, widget ):
        db.set_param( self.db_key, self.get_active() )

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

class PNotebook( Notebook ):
    def __init__( self, key ):
        super( PNotebook, self ).__init__()

        self.db_key = key
        self.restored = False

        self.connect( 'switch-page', self.tab_switch_event )

    def restore_tab( self ):
        self.set_current_page( db.get_param( self.db_key + ':current_tab',
                                             self.get_current_page() ) )
        self.restored = True

    def tab_switch_event( self, widget, page, page_num ):
        if not self.restored:
            return False
        db.set_param( self.db_key + ':current_tab', page_num )

class PWindow( Window ):
    def __init__( self, key, type = WINDOW_TOPLEVEL ):
        super( PWindow, self ).__init__( type )

        self.db_key = key

        width, height = self.get_size()
        x, y = self.get_position()

        width = db.get_param( self.db_key + ':width', width )
        height = db.get_param( self.db_key + ':height', height )
        x = db.get_param( self.db_key + ':xpos', x )
        y = db.get_param( self.db_key + ':ypos', y )

        self.set_default_size( width, height )
        self.move( x, y )

        self.connect( 'delete-event', self.destroy_event )
        self.connect( 'destroy-event', self.destroy_event )

    def destroy_event( self, widget, event ):
        print 'Destroying %s' % str( self )

        width, height = self.get_size()
        x, y = self.get_position()

        db.set_param( self.db_key + ':width', width )
        db.set_param( self.db_key + ':height', height )
        db.set_param( self.db_key + ':xpos', x )
        db.set_param( self.db_key + ':ypos', y )

class LabelItem( HBox ):
    def __init__( self, child, label = None, homogenous = False, spacing = 0 ):
        super( LabelItem, self ).__init__( homogenous, spacing )

        if label:
            self.label = Label( label + ':' )
        else:
            self.label = Label( '' )
        self.label.show()
            
        self.pack_start( self.label, True, False, 0 )
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

class ClickableTextTag( TextTag ):
    def __init__( self,
                  click_action = None,
                  right_click_action = None,
                  double_click_action = None,
                  triple_click_action = None,
                  name = None ):
        self.simple_click = False
        
        super( ClickableTextTag, self ).__init__( name )

        self.click_action = click_action
        self.right_click_action = right_click_action
        self.double_click_action = double_click_action
        self.triple_click_action = triple_click_action

        self.connect( 'event', self.click_event )
        self.connect_after( 'event', self.multi_click_event )

    def multi_click_event( self, texttag, widget, event, point ):
        if self.triple_click_action and event.type == gdk._3BUTTON_PRESS:
            dprint( DEBUG_EVENTS,
                    'Triple-click on texttag %(tag)s',
                    tag = texttag.get_property( 'name' ) )
            return self.triple_click_action( texttag, widget, event, point )
        if self.double_click_action and event.type == gdk._2BUTTON_PRESS:
            dprint( DEBUG_EVENTS,
                    'Double-click on texttag %(tag)s',
                    tag = texttag.get_property( 'name' ) )
            return self.double_click_action( texttag, widget, event, point )
        
        
    def click_event( self, texttag, widget, event, point ):
        buf = None
        if hasattr( widget, 'get_buffer' ):
            buf = point.get_buffer()
        if buf and hasattr( buf, 'icon_click' ) and buf.icon_click:
            return False

        if ( self.right_click_action and
             event.type == gdk.BUTTON_PRESS and
             event.button == 3 ):
            dprint( DEBUG_EVENTS,
                    'Right click on texttag %(tag)s',
                    tag = texttag.get_property( 'name' ) )
            return self.right_click_action( texttag, widget, event, point )
        if event.type == gdk.BUTTON_PRESS:
            dprint( DEBUG_EVENTS,
                    'Button down on texttag %(tag)s',
                    tag = texttag.get_property( 'name' ) )
            buf.simple_click = True
        if event.type == gdk.MOTION_NOTIFY:
            buf.simple_click = False
        if self.click_action and event.type == gdk.BUTTON_RELEASE:
            dprint( DEBUG_EVENTS,
                    'Button up on texttag %(tag)s',
                    tag = texttag.get_property( 'name' ) )
            if buf.simple_click and event.button == 1:
                dprint( DEBUG_EVENTS,
                        'Simple click' )
                return self.click_action( texttag, widget, event, point )

class UserIcon( Image ):
    def __init__( self ):
        super( Image, self ).__init__()

        self.mark = None
        self.simple_click = False

        self.connect( 'event', self.click_event )

    def get_tweet_bounds( self, tag_type, move_start = True ):
        buf = self.mark.get_buffer()
        table = buf.get_tag_table()
        tweet = table.lookup( tag_type )
        
        start = buf.get_iter_at_mark( self.mark )
        if move_start and not start.forward_to_tag_toggle( tweet ):
            return False
        end = start.copy()
        if not end.forward_to_tag_toggle( tweet ):
            return False

        return buf, start, end
        
    def click_event( self, widget, event ): 
        ret = False

        if event.type == gdk._2BUTTON_PRESS:
            dprint( DEBUG_EVENTS,
                    'Double-click on: %(widget)s',
                    widget = self )
            if event.button != 1:
                return False

            bounds = self.get_tweet_bounds( 'tweet' )
            if not bounds:
                return False
            buf, start, end = bounds

            buf.select_range( start, end )

            self.mark.get_buffer().icon_click = False
            self.simple_click = False 
            return True

        if event.type == gdk.BUTTON_PRESS:
            if event.button != 1:
                return False 
            self.mark.get_buffer().icon_click = True
            self.simple_click = True
            ret = False
        if event.type == gdk.MOTION_NOTIFY:
            self.mark.get_buffer().icon_click = False
            self.simple_click = False
            ret = False
        if self.simple_click and event.type == gdk.BUTTON_RELEASE:
            if event.button != 1:
                return False
            dprint( DEBUG_EVENTS,
                    'Click on: %(widget)s',
                    widget = self )
            if self.mark and self.mark.get_buffer():
                point = self.mark.get_buffer().get_iter_at_mark( self.mark )
                self.mark.get_buffer().place_cursor( point )
            self.mark.get_buffer().icon_click = False
            self.simple_click = False
            ret = False
        elif event.type == gdk.BUTTON_RELEASE:
            ret = False

        return ret

class TweetTextBuffer( TextBuffer ):
    def __init__( self, table = None, parent = None ):
        self.parent = parent
        
        super( TweetTextBuffer, self ).__init__( table )

        self.setup_tags()

        self.custom_tags = { 'from' : ({},
                                       { 'click_action' : self.named_tweet_click,
                                         'right_click_action' :
                                         self.named_tweet_right_click
                                         }),
                             'id' : ({},
                                     { 'right_click_action' :
                                       self.id_tweet_right_click
                                       }),
                             }

    def setup_tags( self ):
        table = self.get_tag_table()

        for tag, properties, actions in \
                [ ('none', {}, None),
                  ('start',
                   { 'foreground' : '#222244' },
                   None),
                  ('header',
                   { 'weight' : 550, },
                   None),
                  ('client',
                   { 'foreground' : '#666666' },
                   None),
                  ('hashtag',
                   { 'foreground' : '#8B864E' },
                   None),
                  ('separator',
                   { 'size-points' : 3 },
                   None),
                  ('username',
                   { 'foreground' : '#551A8B' },
                   None),
                  ('url',
                   { 'foreground' : '#4169E1',
                     'underline' : pango.UNDERLINE_SINGLE
                     },
                   { 'click_action' : self.url_click } ),
                  ('time',
                   { 'foreground' : '#666666', },
                   None),
                  ('full_tweet', {}, None),
                  ('tweet', {},
                   { 'double_click_action' : self.tweet_select } )]:
            if not properties:
                properties = {}
            if not actions:
                actions = {}
            tag = ClickableTextTag( name = tag, **actions )
            for prop, value in properties.items():
                tag.set_property( prop, value )
            table.add( tag )

    def insert_tag_list( self, point, tag_list ):
        for text, tag in tag_list:
            if type( text ) not in (str, unicode):
                continue
            
            table = self.get_tag_table()
            
            if type( tag ) not in (list, tuple, set):
                tag = [ tag ]
                
            new_tag = []
            for t in tag:
                if not t:
                    t = 'none'
                if is_custom_tag( t ):
                    if not self.custom_tags.has_key( custom_tag_name( t ) ):
                        continue
                    if not table.lookup( t ):
                        ( properties,
                          actions ) = self.custom_tags[ custom_tag_name( t ) ]
                        if not properties:
                            properties = {}
                        if not actions:
                            actions = {}
                        tmp_tag = ClickableTextTag( name = t,
                                                    **actions )
                        for prop, value in properties.items():
                            tmp_tag.set_property( prop, value )
                        table.add( tmp_tag )

                new_tag.append( t )
            self.insert_with_tags_by_name( point, text, *new_tag )

    def insert_images( self, images ):
        dprint( DEBUG_MESSAGES,
                'Inserting images' )
        
        if not self.parent:
            return

        x = 4
        for img in images:
            if not img.mark:
                continue
            point = self.get_iter_at_mark( img.mark )
            y, height = self.parent.get_line_yrange( point )
            y += 4

            img.show()
            self.parent.add_child_in_window( img,
                                             TEXT_WINDOW_TEXT,
                                             x, y )
            
    def named_tweet_click( self, texttag, widget, event, point ):
        pass

    def named_tweet_right_click( self, texttag, widget, event, point ):
        self.right_click_tag = texttag
        self.right_click_mark = self.create_mark( None, point, False )

        start = point.copy()

        flag = start.backward_to_tag_toggle( texttag )
        if not flag:
            return False

        flag = point.forward_to_tag_toggle( texttag )
        if not flag:
            return False

        self.right_click_text = self.get_text( start, point )

    def id_tweet_right_click( self, texttag, widget, event, point ):
        tag_name = texttag.get_property( 'name' )

        self.right_click_id = long( custom_tag_payload( tag_name ) )

    def tweet_select( self, texttag, widget, event, point ):
        start = point.copy()

        flag = start.backward_to_tag_toggle( texttag )
        if not flag:
            return False

        flag = point.forward_to_tag_toggle( texttag )
        if not flag:
            return False

        self.select_range( start, point )

        return True

    def full_tweet_select( self, texttag, widget, event, point ):
        start = point.copy()

        flag = start.backward_to_tag_toggle( texttag )
        if not flag:
            return False

        flag = point.forward_to_tag_toggle( texttag )
        if not flag:
            return False

        self.select_range( start, point )

        return True

    def url_click( self, texttag, widget, event, point ):
        start = point.copy()

        flag = start.backward_to_tag_toggle( texttag )
        if not flag:
            return False

        flag = point.forward_to_tag_toggle( texttag )
        if not flag:
            return False

        url = self.get_slice( start, point )

        webbrowser.open( url )
        return False

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
