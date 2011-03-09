from gtk import *

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

    dialog.vbox.pack_end(hbox, True, True, 0)

    dialog.show_all()
    dialog.run()

    text = entry.get_text()
    dialog.destroy()

    return text
