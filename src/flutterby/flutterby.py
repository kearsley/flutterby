import gobject, gtk, pango
import os, sys, string, threading, time, unicodedata

import flutterby_db as db
import flutterby_resources as res
import flutterby_tweets as tweets
import flutterby_widgets as w
import flutterby_shorten as shorten

TWEET_LENGTH = 140
TYPING_DELAY = -1

class ViewPane:
    def __init__( self, parent, tab, timelines ):
        self.simple_click = False
        self.parent = parent
        self.tab = tab
        self.timelines = timelines
        
        self.box = w.ScrolledWindow()
        self.box.set_policy( w.POLICY_AUTOMATIC, w.POLICY_AUTOMATIC )

        self.list = w.TextView( self.timelines.buffer )
        self.timelines.new_buffer()
        self.list.set_wrap_mode( w.WRAP_WORD )
        self.list.set_editable( False )

        self.timelines.add_listener( self )
        
        self.list.show()
        self.box.add_with_viewport( self.list )
        self.box.show()

    def notify( self, message ):
        if message == 'timeline buffer updated':
            self.list.set_buffer( self.timelines.buffer )

class EntryPane:
    def __init__( self, parent, tab ):
        self.last_changed = 0
        self.parent = parent
        self.tab = tab
        
        self.box = w.HBox( False, 5 )

        # The text field
        self.text_entry = w.TextView()
        self.text_entry.set_wrap_mode( w.WRAP_WORD )

        self.text_entry.connect( 'key_release_event', self.key_event )
        self.text_entry.get_buffer().connect( 'changed', self.typing_event )
        self.text_entry.set_events( w.gdk.KEY_RELEASE )

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

    def key_event( self, widget, event ):
        keyname = w.gdk.keyval_name( event.keyval )
        if keyname == 'Return' and event.state == 0:
            self.send_event( widget, True )

    def typing_event( self, widget ):
        if time.time() - self.last_changed < TYPING_DELAY:
            return False
        
        buf = self.text_entry.get_buffer()
        start, end = buf.get_bounds()
        
        text = unicode( buf.get_text( start, end ),
                        'utf-8' )
        norm = unicodedata.normalize( 'NFC', text )
        remaining = TWEET_LENGTH - len( norm )

        self.character_count.set_text( unicode( remaining ) )

        self.last_changed = time.time()
        
    def send_event( self, widget, by_typing = False ):
        self.start_spinner()

        account = self.parent.tab_items[ self.tab ][ 'account' ]

        buf = self.text_entry.get_buffer()
        point = buf.get_iter_at_mark( buf.get_insert() )
        if by_typing:
            buf.backspace( point, False, True )

        start, end = buf.get_bounds()
        text = buf.get_text( start, end )

        text = text.strip()
        while len( text ) and text[-1] == '\n':
            text = text[:-1]

        print account, text
        if tweets.tweet( account, text ):
            buf.delete( start, end )
            self.parent.refresh_event( widget )
            self.stop_spinner()
        self.stop_spinner()    

    def start_spinner( self ):
        self.spinner.set_sensitive( True )
        self.spinner.start()

    def stop_spinner( self ):
        self.spinner.stop()
        self.spinner.set_sensitive( False )        

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
    <menu action="Edit">
      <menuitem action="Cut" />       
      <menuitem action="Copy" />      
      <menuitem action="Paste" /> 
      <menuitem action="Shorten and Paste" /> 
    </menu>
  </menubar>
</ui>'''

class MainWindow:
    def __init__( self, wname ):
        self.locks = { 'timelines' : threading.Lock(),
                       }
        self.refresher = tweets.RefreshTimelines( self )
        
        self.window = w.PWindow( wname, w.WINDOW_TOPLEVEL )
        self.window.set_title( 'Flutterby' )
        self.window.set_icon_from_file( res.image_path( 'flutterby_icon' ) )
        self.window.connect( 'delete_event', self.delete_event )

        windowbox = w.VBox( False, 0 )        

        self.tabs = w.PNotebook( 'main_tabs' )
        
        self.tab_items = {}

        for account in db.list_accounts():
            tab_item = { 'account' : account }
            mainbox = w.VBox( False, 0 )

            timelines = tweets.TimelineSet( [] )
            timelines.add( tweets.Timeline( account ) )
            tab_item[ 'timelines' ] = timelines
            
            # The reading/viewing area
            view = ViewPane( self, self.tabs.get_n_pages(), timelines )
            tab_item[ 'view' ] = view

            # The editing area
            entry = EntryPane( self, self.tabs.get_n_pages() )
            tab_item[ 'entry' ] = entry

            mainbox.pack_start( view.box, True, True, 0 )

            separator = w.HSeparator()
            separator.show()
            mainbox.pack_start( separator, False, True, 2 )

            mainbox.pack_start( entry.box, False, False, 2 )

            timelines.refresh( limit = None, network = False )
            mainbox.show() 

            self.tab_items[ self.tabs.get_n_pages() ] = tab_item

            self.tabs.append_page( mainbox, w.Label( account ) )

        if len( self.tab_items.keys() ) <= 1:
            self.tabs.set_show_tabs( False )

        # The main menu
        self.setup_ui()
        self.menubar = self.uimanager.get_widget( '/MenuBar' )
        windowbox.pack_start( self.menubar, False, True, 0 )

        self.tabs.restore_tab()
        self.tabs.show()
        windowbox.pack_start( self.tabs, True, True, 0 )
        windowbox.show()
        self.window.add( windowbox )

        current_page = self.tabs.get_current_page()
        if current_page >= 0:
            self.tab_items[ current_page ][ 'entry' ].text_entry.grab_focus()

        def start_refresher():
            self.refresher.start()
        threading.Timer( 4.0, start_refresher ).start()

    def current_page_item( self, key ):
        current_page = self.tabs.get_current_page()
        return self.tab_items[ current_page ][ key ]        

    def entry( self ):
        return self.current_page_item( 'entry' )

    def view( self ):
        return self.current_page_item( 'view' )

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
        w.main_quit()
        return False

    def refresh_event( self, widget ):
        refresher = tweets.RefreshTimelines( self, loop = False )
        refresher.start()

    def accounts_event( self, widget ):
        aw = AccountsWindow( self )
        aw.window.show()

    def preferences_event( self, widget ):
        pw = PreferencesWindow( self )
        pw.window.show()

    def following_event( self, widget ):
        fw = FollowingWindow( self )
        fw.window.show()

    def cut_event( self, widget ):
        foc = self.window.get_focus()
        

        if not ( hasattr( foc, 'get_editable' ) and foc.get_editable() ):
            return False

        foc.do_cut_clipboard( foc )
        return True

    def copy_event( self, widget ):
        foc = self.window.get_focus()

        foc.do_copy_clipboard( foc )
        return True

    def paste_event( self, widget ):
        foc = self.window.get_focus()

        if not ( hasattr( foc, 'get_editable' ) and foc.get_editable() ):
            return False

        foc.do_paste_clipboard( foc )
        return True

    def shorten_paste_event( self, widget ):
        buf = self.entry().text_entry.get_buffer()

        point = buf.get_iter_at_mark( buf.get_insert() )
        clipboard = w.Clipboard()

        def paste( cb, sd, it ):
            url = shorten.shorten( sd )
            buf.insert( point, url )

        clipboard.request_text( paste, point )

    def setup_ui( self ):
        self.uimanager = w.UIManager()

        accel = self.uimanager.get_accel_group()
        self.window.add_accel_group( accel )
        
        actiongroup = w.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup
        self.actiongroup.add_actions( [ ('Flutterby', None, '_Flutterby'),
                                        ('Accounts', None,
                                         '_Accounts...', '<Control><Shift>A',
                                         'Show and configure accounts',
                                         self.accounts_event),
                                        ('Following', None,
                                         '_Following...', '<Control><Shift>F',
                                         'Configure which accounts you are '
                                         'following',
                                         self.following_event),
                                        ('Refresh', None,
                                         '_Refresh', '<Control>R',
                                         'Refresh the twitter timeline',
                                         self.refresh_event),
                                        ('Preferences', None,
                                         '_Preferences...', None,
                                         'Configure the application as a whole',
                                         self.preferences_event),
                                        ('Quit', w.STOCK_QUIT,
                                         '_Quit', None,
                                         'Quit the Program',
                                         self.delete_event),
                                        ('Edit', None, '_Edit'),
                                        ('Cut', w.STOCK_CUT,
                                         'Cut', None,
                                         'Cut text',
                                         self.cut_event),
                                        ('Copy', w.STOCK_COPY,
                                         'Copy', None,
                                         'Copy text',
                                         self.copy_event),
                                        ('Paste', w.STOCK_PASTE,
                                         'Paste', None,
                                         'Paste text',
                                         self.paste_event),
                                        ('Shorten and Paste', w.STOCK_PASTE,
                                         'Shorten and Paste', '<Shift><Control>V',
                                         'Pass text through an URL shortener '
                                         'before pasting it',
                                         self.shorten_paste_event),
                                        ] )

        self.uimanager.insert_action_group( self.actiongroup, 0 )

        self.uimanager.add_ui_from_string( UI )

    def set_timelines( self, timelines ):
        self.lock( 'timelines' )
        self.timelines = timelines
        self.release( 'timelines' )        

class AccountsWindow:
    def __init__( self, parent ):
        self.parent = parent
        
        self.window = w.PWindow( 'accounts', w.WINDOW_TOPLEVEL )
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

    def make_account_dialog( self ):
        ad = w.PWindow( 'add_account' )

        grid = w.Table( rows = 2, columns = 3 )

        stage1_label = w.Label( 'Enter the account name:' )
        stage1_label.set_alignment( 0, 0.5 )
        stage1_label.show()

        stage1_entry = w.Entry()
        stage1_entry.show()

        stage1_button = w.Button( 'Request a PIN' )
        stage1_button.set_sensitive( False )
        stage1_button.show()
        
        stage2_label = w.Label( 'Enter the PIN given to you by Twitter:' )
        stage2_label.set_alignment( 0, 0.5 )
        stage2_label.show()

        stage2_entry = w.Entry()
        stage2_entry.set_sensitive( False )
        stage2_entry.show()
        
        stage2_button = w.Button( 'Register account' )
        stage2_button.set_sensitive( False )
        stage2_button.show()

        def stage1_entry_changed( widget ):
            if stage1_entry.get_text_length() > 0:
                stage1_button.set_sensitive( True )
            else:
                stage1_button.set_sensitive( False )                
        stage1_entry.connect( 'changed', stage1_entry_changed )

        def stage1_button_clicked( widget ):
            self.auth = tweets.authenticate( stage1_entry.get_text() )

            for widget in (stage1_label, stage1_entry, stage1_button,):
                widget.set_sensitive( False )
            for widget in (stage2_label, stage2_entry,):
                widget.set_sensitive( True )

            return True
        stage1_button.connect( 'clicked', stage1_button_clicked )

        def stage2_entry_changed( widget ):
            if stage2_entry.get_text_length() > 0:
                stage2_button.set_sensitive( True )
            else:
                stage2_button.set_sensitive( False )                
        stage2_entry.connect( 'changed', stage2_entry_changed )

        def stage2_button_clicked( widget ):
            tweets.authenticate2( stage1_entry.get_text(),
                                  stage2_entry.get_text(),
                                  self.auth )

            self.accounts.refresh_model()
            ad.destroy()
            return True
        stage2_button.connect( 'clicked', stage2_button_clicked )

        grid.attach( stage1_label, 0, 1, 0, 1, w.FILL, w.FILL )
        grid.attach( stage1_entry, 1, 2, 0, 1, w.FILL, w.FILL )
        grid.attach( stage1_button, 2, 3, 0, 1, w.FILL, w.FILL )
        grid.attach( stage2_label, 0, 1, 1, 2, w.FILL, w.FILL )
        grid.attach( stage2_entry, 1, 2, 1, 2, w.FILL, w.FILL )
        grid.attach( stage2_button, 2, 3, 1, 2, w.FILL, w.FILL )

        grid.show()

        ad.add( grid )
        ad.show()

        return ad

    def add_event( self, widget ):
        ad = self.make_account_dialog()

    def delete_event( self, widget ):
        account = self.get_selected_account()
        if not account:
            return

        db.delete_account( account )
        self.accounts.refresh_model()
    
    def edit_event( self, widget ):
        pass

class FollowingWindow:
    def __init__( self, parent ):
        self.parent = parent

        self.window = w.PWindow( 'following', w.WINDOW_TOPLEVEL )
        self.window.set_title( 'Following' )

        mainbox = w.VBox( False, 0 )

        self.accounts = w.DBTreeView( 'accounts', [ ('name', str, 'Account',) ] )
        selection = self.accounts.get_selection()
        selection.set_mode( w.SELECTION_SINGLE )
        selection.connect( 'changed', self.selection_changed )
        
        self.accounts.show()
        mainbox.pack_start( self.accounts, True, True, 0 )        
        
        mainbox.show()
        self.window.add( mainbox )
    
class PreferencesWindow:
    def change_refresh( self, widget ):
        self.parent.refresh_event( widget )
    
    def __init__( self, parent ):
        self.parent = parent
        
        self.window = w.PWindow( 'preferences', w.WINDOW_TOPLEVEL )
        self.window.set_title( 'Preferences' )

        mainbox = w.VBox( False, 0 )

        grid = w.Table( rows = 3, columns = 2 )

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
                     ('1 day', 1440),
                     ('Never', -1),]:
            delay_model.append( row )
        delay = w.PComboBoxText( key = 'delay', model = delay_model )
        delay.restore_value()
        delay_label = w.Label( 'Delay between checking for new tweets' )
        delay_label.set_alignment( 0, 0.5 )

        tweet_count_model = w.ListStore( str, int )
        for row in [ ('10', 10),
                     ('15', 15),
                     ('20', 20),
                     ('25', 25),
                     ('30', 30),
                     ('40', 40),
                     ('50', 50),
                     ('100', 100),
                     ('200', 200),
                     ('500', 500),
                     ('1000', 1000),
                     ('Unlimited', -1) ]:
            tweet_count_model.append( row )
        tweet_count = w.PComboBoxText( key = 'tweet_count',
                                       model = tweet_count_model )
        tweet_count.connect( 'changed', self.change_refresh )
        tweet_count.restore_value()
        tweet_count_label = w.Label( 'Maximum tweets to display' )
        tweet_count_label.set_alignment( 0, 0.5 )

        tweet_age_model = w.ListStore( str, int )
        for row in [ ('1 hour', 1),
                     ('2 hours', 2),
                     ('3 hours', 3),
                     ('6 hours', 6),
                     ('12 hours', 12),
                     ('1 day', 24),
                     ('2 days', 48),
                     ('3 days', 72),
                     ('4 days', 96),
                     ('1 week', 168),
                     ('2 weeks', 336),
                     ('1 month', 744),
                     ('6 months', 4360),
                     ('1 year', 8760),
                     ('Unlimited', -1) ]:
            tweet_age_model.append( row )
        tweet_age = w.PComboBoxText( key = 'tweet_age',
                                     model = tweet_age_model )
        tweet_age.connect( 'changed', self.change_refresh )
        tweet_age.restore_value()
        tweet_age_label = w.Label( 'Maximum age of tweets to display' )
        tweet_age_label.set_alignment( 0, 0.5 )

        for widget in [ delay, delay_label,
                        tweet_count, tweet_count_label,
                        tweet_age, tweet_age_label ]:
            widget.show()

        grid.attach( delay_label, 0, 1, 0, 1, w.FILL, w.FILL )
        grid.attach( tweet_count_label, 0, 1, 1, 2, w.FILL, w.FILL )
        grid.attach( tweet_age_label, 0, 1, 2, 3, w.FILL, w.FILL )
        grid.attach( delay, 1, 2, 0, 1, w.FILL, w.FILL )
        grid.attach( tweet_count, 1, 2, 1, 2, w.FILL, w.FILL )
        grid.attach( tweet_age, 1, 2, 2, 3, w.FILL, w.FILL )

        grid.show()
        mainbox.pack_start( grid, False, True, 0 )

        separator = w.HSeparator()
        separator.show()
        mainbox.pack_start( separator, False, True, 2 )

        show_username = w.PCheckButton( 'show_name', 'Show full user name' )
        show_username.connect( 'toggled', self.change_refresh )
        show_username.show()
        mainbox.pack_start( show_username, False, False, 0 )

        show_retweets = w.PCheckButton( 'show_retweets', 'Show retweets' )
        show_retweets.connect( 'toggled', self.change_refresh )
        show_retweets.show()
        mainbox.pack_start( show_retweets, False, False, 0 )

        show_client = w.PCheckButton( 'show_client', 'Show posting client' )
        show_client.connect( 'toggled', self.change_refresh )
        show_client.show()
        mainbox.pack_start( show_client, False, False, 0 )

        separator = w.HSeparator()
        separator.show()
        mainbox.pack_start( separator, False, True, 2 )

        notify_new = w.PCheckButton( 'new_tweet_notify',
                                     'Display notifications on new tweets' )
        notify_new.show()
        mainbox.pack_start( notify_new, False, False, 0 )

        mainbox.show()
        self.window.add( mainbox )

def main():
    gobject.threads_init()

    res.setup_user_paths()

    mw = MainWindow( 'main' )
    mw.window.show()
    
    w.main()
    return 0

if __name__ == '__main__':
    sys.exit( main() )
