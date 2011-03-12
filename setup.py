from cx_Freeze import setup, Executable

#This is a list of files to install, and where
#(relative to the 'root' dir, where setup.py is)
#You could be more specific.
files = ["src/*.py", "src/resources/*"]

setup(name = "flutterby",
      version = "0.2",
      description = "A Twitter client written in Python/PyGTK",
      author = "Kearsley Schieder-Wethy",
      author_email = "kearsley@frimble.net",
      url = "http://frimble.net/cms/flutterby",
      
      executables = [Executable( 'flutterby.py' )],
      
      long_description = """A Twitter client written in Python/PyGTK

It is currently under basic development, but has the following features:

 * Authentication via OAuth
 * Watching multiple Twitter accounts
 * Highlighting of tweets
 * Clickable URLs
 * The option to shorten an URL in the clipboard before pasting."""
      #
      #This next part it for the Cheese Shop, look a little down the page.
      #classifiers = []     
) 
