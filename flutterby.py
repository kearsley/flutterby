import pygtk
import gtk
import sys,string

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
        gtk.main_quit()
        return False
    
    def __init__( self ):
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self.window.connect( 'delete_event', self.delete_event )

        mainbox = gtk.VBox( False, 0 )

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
