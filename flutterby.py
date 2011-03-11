import gobject, gtk, pango
import sys, string, threading

import flutterby_db as db
import flutterby_tweets as tweets
import flutterby_widgets as w

UI = '''<ui>
  <menubar name="MenuBar">
    <menu action="Flutterby">
      <menuitem action="Accounts" />       
      <menuitem action="Refresh" />      
      <separator />
      <menuitem action="Preferences" />      
      <separator />
      <menuitem action="Quit" />
    </menu>
  </menubar>
</ui>'''

class ViewPane:
    def __init__( self, parent ):
        self.parent = parent
        
        self.box = w.ScrolledWindow()

        self.list = w.TextView( self.parent.timelines.buffer )
        self.list.set_wrap_mode( w.WRAP_WORD )
        self.list.set_editable( False )
        
        self.list.show()
        self.box.add_with_viewport( self.list )
        self.box.show()

class EntryPane:
    def __init__( self, parent ):
        self.parent = parent
        
        self.box = w.HBox( False, 5 )

        # The text field
        self.text_entry = w.TextView()
        self.text_entry.set_wrap_mode( w.WRAP_WORD )

        self.text_entry.show()
        self.box.pack_start( self.text_entry, True, True, 2 )

        rbox = w.VBox( False, 2 )

        # The count of remaining characters in the tweet
        self.character_count = w.Label( '140' )
        self.character_count.show()

        self.spinner = w.Spinner()
        self.spinner.set_sensitive( False )
        self.spinner.show()

        rbox.pack_start( self.character_count, False, False, 0 )
        rbox.pack_start( self.spinner, False, False, 0 )
        rbox.show()

        self.box.pack_start( rbox, False, False, 2 )
        self.box.show()

    def start_spinner( self ):
        self.spinner.set_sensitive( True )
        self.spinner.start()

    def stop_spinner( self ):
        self.spinner.stop()
        self.spinner.set_sensitive( False )        

class MainWindow:
    def get_lock( self, lock ):
        l = self.locks.get( lock, None )
        if not l:
            raise Exception( 'The lock "%s" does not appear to exist.' % lock )
        return l
    
    def lock( self, lock ):
        l = self.get_lock( lock )
        l.acquire()

    def release( self, lock ):
        l = self.get_lock( lock )
        l.release()
    
    def delete_event( self, widget, event = None, data = None ):
        width, height = self.window.get_size()
        x, y = self.window.get_position()

        db.set_param( 'width', width )
        db.set_param( 'height', height )
        db.set_param( 'xpos', x )
        db.set_param( 'ypos', y )
        
        w.main_quit()
        return False

    def refresh_event( self, event ):
        refresher = tweets.RefreshTimelines( self, loop = False )
        refresher.start()

    def accounts_event( self, event ):
        aw = AccountsWindow()
        aw.window.show()

    def preferences_event( self, event ):
        pw = PreferencesWindow()
        pw.window.show()

    def setup_ui( self ):
        self.uimanager = w.UIManager()

        accel = self.uimanager.get_accel_group()
        self.window.add_accel_group( accel )
        
        actiongroup = w.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup
        self.actiongroup.add_actions( [ ('Quit', w.STOCK_QUIT,
                                         '_Quit', None,
                                         'Quit the Program',
                                         self.delete_event),
                                        ('Accounts', None,
                                         '_Accounts', '<Control><Shift>A',
                                         'Show and configure accounts',
                                         self.accounts_event),
                                        ('Refresh', None,
                                         '_Refresh', '<Control>R',
                                         'Refresh the twitter timeline',
                                         self.refresh_event),
                                        ('Preferences', None,
                                         '_Preferences', None,
                                         'Configure the application as a whole',
                                         self.preferences_event),
                                        ('Flutterby', None, '_Flutterby'),
                                        ] )

        self.uimanager.insert_action_group( self.actiongroup, 0 )

        self.uimanager.add_ui_from_string( UI )

    def set_timelines( self, timelines ):
        self.lock( 'timelines' )
        self.timelines = timelines
        self.release( 'timelines' )
        
    def __init__( self ):
        self.locks = { 'timelines' : threading.Lock(),
                       }
        self.timelines = tweets.TimelineSet()
        self.timelines.add_list( [ tweets.Timeline( acc )
                                   for acc in db.list_accounts() ] )
        self.refresher = tweets.RefreshTimelines( self )
        
        self.window = w.Window( w.WINDOW_TOPLEVEL )
        self.window.connect( 'delete_event', self.delete_event )

        width = db.get_param( 'width', 200 )
        height = db.get_param( 'height', 600 )
        x = db.get_param( 'xpos', 0 )
        y = db.get_param( 'ypos', 0 )
        
        self.window.set_default_size( width, height )
        self.window.move( x, y )
        
        mainbox = w.VBox( False, 0 )

        # The reading/viewing area
        self.view = ViewPane( self )

        # The editing area
        self.entry = EntryPane( self )

        # The main menu
        self.setup_ui()
        self.menubar = self.uimanager.get_widget( '/MenuBar' )
        
        mainbox.pack_start( self.menubar, False, True, 0 )
        mainbox.pack_start( self.view.box, True, True, 0 )

        separator = w.HSeparator()
        separator.show()
        mainbox.pack_start( separator, False, True, 2 )
        
        mainbox.pack_start( self.entry.box, False, False, 2 )

        mainbox.show()
        self.window.add( mainbox )

        initial_update = tweets.RefreshTimelines( self,
                                                  limit = None,
                                                  loop = False )
        def start_refresher():
            self.refresher.start()
        threading.Timer( 5.0, start_refresher ).start()

class AccountsWindow:
    def get_selected_account( self ):
        model, row = self.accounts.get_selection().get_selected()
        if not row:
            return None

        return model.get_value( row, 0 )
    
    def selection_changed( self, widget ):
        if not self.get_selected_account():
            sensitive = False
        else:
            sensitive = True
        for widget in [ self.delete_button, ]:
            widget.set_sensitive( sensitive )

    def add_event( self, widget ):
        account = w.prompt_dialog( 'What is the name of the Twitter account which '
                                   'you would like to add?',
                                   'Account name' )
        tweets.authenticate( account )
        
        self.accounts.refresh_model()
        return account
    
    def delete_event( self, widget ):
        account = self.get_selected_account()
        if not account:
            return

        db.delete_account( account )
        self.accounts.refresh_model()
    
    def edit_event( self, widget ):
        pass
    
    def __init__( self ):
        self.window = w.Window( w.WINDOW_TOPLEVEL )
        self.window.set_title( 'Accounts' )
        self.window.set_default_size( 200, 400 )

        mainbox = w.HBox( False, 0 )

        self.accounts = w.DBTreeView( 'accounts', [ ('name', str, 'Account',) ] )
        selection = self.accounts.get_selection()
        selection.set_mode( w.SELECTION_SINGLE )
        selection.connect( 'changed', self.selection_changed )
        
        self.accounts.show()
        mainbox.pack_start( self.accounts, True, True, 0 )

        buttonbox = w.VBox( False, 0 )

        self.add_button = w.Button( stock = w.STOCK_ADD )
        self.add_button.connect( 'clicked', self.add_event )
        
        self.delete_button = w.Button( stock = w.STOCK_DELETE )
        self.delete_button.connect( 'clicked', self.delete_event )
        
        # self.edit_button = w.Button( label = 'Edit' )

        self.selection_changed( self.accounts )
        for widget in reversed( [ self.add_button,
                                  self.delete_button, ] ):
            widget.show()
            buttonbox.pack_end( widget, False, False, 0 )

        buttonbox.show()
        mainbox.pack_start( buttonbox, False, False, 0 )
            
        mainbox.show()
        self.window.add( mainbox )

class PreferencesWindow:
    def __init__( self ):
        self.window = w.Window( w.WINDOW_TOPLEVEL )
        self.window.set_title( 'Preferences' )

        self.window.move( 200, 200 )

        mainbox = w.VBox( False, 0 )

        delay_model = w.ListStore( str, int )
        for row in [ ('5 minutes', 5),
                     ('10 minutes', 10),
                     ('15 minutes', 15),
                     ('30 minutes', 30),
                     ('1 hour', 60),
                     ('2 hours', 120),
                     ('3 hours', 180),
                     ('4 hours', 240),
                     ('5 hours', 300),
                     ('6 hours', 360),
                     ('12 hours', 720),
                     ('1 day', 1440) ]:
            delay_model.append( row )
        delay = w.PComboBoxText( key = 'delay', model = delay_model )
        delay.restore_value()
        delay_box = w.LabelItem( delay, 'Delay between checking for new tweets' )

        for widget in [ delay, delay_box ]:
            widget.show()

        mainbox.pack_start( delay_box, False, False, 0 )

        mainbox.show()
        self.window.add( mainbox )

def main():
    gobject.threads_init()

    mw = MainWindow()
    mw.window.show()
    
    w.main()
    return 0

if __name__ == '__main__':
    sys.exit( main() )
