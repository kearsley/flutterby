from distutils.core import setup

#This is a list of files to install, and where
#(relative to the 'root' dir, where setup.py is)
#You could be more specific.
files = ["things/*"]

setup(name = "flutterby",
      version = "0.2",
      description = "A Twitter client written in Python/PyGTK",
      author = "Kearsley Schieder-Wethy",
      author_email = "kearsley@frimble.net",
      url = "http://frimble.net/cms/flutterby",
      
      #Name the folder where your packages live:
      #(If you have other packages (dirs) or modules (py files) then
      #put them into the package directory - they will be found 
      #recursively.)
      packages = ['src'],
      
      #'package' package must contain files (see list above)
      #I called the package 'package' thus cleverly confusing the whole issue...
      #This dict maps the package name =to=> directories
      #It says, package *needs* these files.
      package_data = {'package' : files },
      
      #'runner' is in the root.
      scripts = ["flutterby"],
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
