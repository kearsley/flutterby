import pygtk
import gtk
import sys,string

import flutterby_db as db

class MainMenu:
    def __init__( self, menu_items, parent ):
        self.accel = gtk.AccelGroup()

        self.menu_items = menu_items

        item_factory = gtk.ItemFactory( gtk.MenuBar, "<main>", self.accel )
        item_factory.create_items( self.menu_items )

        parent.add_accel_group( self.accel )

        self.menu = item_factory.get_widget( "<main>" )

class ViewPane:
    def __init__( self ):
        self.box = gtk.ScrolledWindow()
        self.box.set_policy( hscrollbar_policy = gtk.POLICY_AUTOMATIC,
                             vscrollbar_policy = gtk.POLICY_ALWAYS )

        self.box.show()

class EntryPane:
    def __init__( self ):
        self.box = gtk.HBox( False, 5 )

        # The text field
        self.text_entry = gtk.TextView()
        self.text_entry.set_wrap_mode( gtk.WRAP_WORD )

        self.text_entry.show()
        self.box.pack_start( self.text_entry, True, True, 5 )

        # The count of remaining characters in the tweet
        self.character_count = gtk.Label( '140' )
        self.character_count.show()
        
        self.box.pack_start( self.character_count, False, False, 5 )
        self.box.show()

class MainWindow:
    def delete_event( self, widget, event, data = None ):
        width, height = self.window.get_size()
        x, y = self.window.get_position()

        db.set_param( 'width', width )
        db.set_param( 'height', height )
        db.set_param( 'xpos', x )
        db.set_param( 'ypos', y )
        
        gtk.main_quit()
        return False
    
    def __init__( self ):
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self.window.connect( 'delete_event', self.delete_event )

        width = db.get_param( 'width', 200 )
        height = db.get_param( 'height', 600 )
        x = db.get_param( 'xpos', 0 )
        y = db.get_param( 'ypos', 0 )
        
        self.window.resize( width, height )
        self.window.move( x, y )
        
        mainbox = gtk.VBox( False, 0 )

        # The main menu
        # self.mainmenu = MainMenu( ( ( "/_Flutterby", None, None, 0, "<Branch>", ),
        #                             ( "/Flutterby/Accounts",
        #                               None, None, 0,
        #                               None, ),
        #                             ( "/_Help", None, None, 0, "<Branch>", ), ),
        #                           self.window )
        # self.mainmenu.menu.show()
        # mainbox.pack_start( self.mainmenu.menu, False, True, 0 ) 
        
        # The reading/viewing area
        self.view = ViewPane()
        mainbox.pack_start( self.view.box, True, True, 0 )

        separator = gtk.HSeparator()
        separator.show()
        mainbox.pack_start( separator, False, True, 2 )
        
        # The editing area
        self.entry = EntryPane()
        mainbox.pack_start( self.entry.box, False, False, 2 )

        mainbox.show()
        self.window.add( mainbox )
        self.window.show()

def main():
    w = MainWindow()
    gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit( main() )
