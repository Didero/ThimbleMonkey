# ThimbleMonkey
An early version of a Python / PySide6 graphical program to view Return To Monkey Island files (and hopefully Thimbleweed Park files later)  
This project is based very much on the work done over at [Dinky Explorer](https://github.com/bgbennyboy/Dinky-Explorer). Thanks!

## How to run
### From release
Just double-click the executable. Easy!

### From Python scripts
#### Initial setup
This project needs some libraries, so you probably want to set up a virtual environment first, to keep these libraries out of your main Python install.
There are some guides on the internet on how to do that, but briefly:
- (**Note**: On MacOS, use 'python3' instead of 'python' for these steps)
- Make sure you have Python installed. Try opening a commandprompt or terminal, and typing 'python --version'. You should get a version number. If you get an error, install Python 3
- Download this project from its GitHub page by clicking the green 'Code' button and selecting 'Download ZIP'. Or use a GIT client to check out the repository
- Extract the download ZIP somewhere, and open a commandprompt or terminal there
- In the commandprompt or terminal, run the command 'python -m pip venv venv'. This creates the virtual environment
- Activate the virtual environment by typing 'venv\Scripts\activate' on Windows or 'source venv/bin/activate' on Linux and MacOS
- Run the command 'python -m pip install -r requirements.txt' to install the required libraries in your new virtual environment
- Now you're done with the setup! Move on to 'Starting ThimbleMonkey'
#### Starting ThimbleMonkey
(**Note**: If you're on MacOS, use 'python3' instead of 'python' for these steps)
- Open a commandprompt or terminal, and navigate to where you extracted ThimbleMonkey
- If you didn't just do the initial setup listed above, activate the virtual environment by typing 'venv\Scripts\activate' on Windows or 'source venv/bin/activate' on Linux and MacOS
- Run the command 'python -m main.py'
- ThimbleMonkey should start now

## Using ThimbleMonkey
### Loading game files
- Click 'File' and select 'Load game folder...'. This opens up a file browser
- Navigate to where your Return To Monkey Island game files are. You can find this location by opening Steam, right-clicking Return To Monkey Island, and selecting 'Manage' and then 'Browse Local Files'. No files show up in the file browser, because you're selecting a whole folder.
- Click 'Select folder'. This makes ThimbleMonkey load all the ggpack files from the game folder. This could take a little while
- The list on the left should have filled with a lot of filenames now. Double-click one to see the file contents on the right
- Some interesting file types: '.ktxbz' file are images, '.otf' and '.ttf' files are fonts, '.yack' files are conversation script files. But I'm sure every file has something interesting in it

### Filtering the file list
On the bottom left, there is a 'Filter' textbox. Type a filename filter in here and press Enter or click the search button next to it, and the file list will be filtered on the entered text.  
This filtering supports wildcards: '?' for a single character, '\*' for multiple characters. Examples: 'Banner_?-hd.ktxbz' lists all the Banner image files, '\*.ktxbz' lists all the image files

### Closing tabs
You can open multiple files. They open in separate tabs.  
Because especially images (files ending in '.ktxbz' or '.png') can take up quite a bit of memory, you can easily close tabs from the 'Tabs' menu. To close a single tab, click the X on the right of the tab

### Saving data
You can get files out of ThimbleMonkey in two ways:
- By clicking the 'File' menu and selecting 'Save current tab data', you can save the data from the current tab just as it is stored in the game files. An image will be saved as a .ktxbz file, for instance
- By clicking the 'File' menu and selecting 'Export current tab data', you can save the data from the current tab in a way that other programs can read. An image will be saved as a PNG file, for instance

## Limitations
- Files from Thimbleweed Park and Delores cannot be loaded yet. This will be added in the future
- The parsing of the main RtMI game script file, 'Weird.dink' is not finished. The results kind of make sense, but not really
- Parsing of the conversation files ('.yack') isn't fully finished yet, but it's already readable
- Music and sound files (files ending in '.bank') are not supported yet. This will be added in the future
- Viewing text and images is slightly clumsy right now. More view controls will be added in the future
- Some actions take a while, which freezes the whole window. A progress bar for these actions will probably be added in the future
- No error handling, so if something goes wrong, ThimbleMonkey just quietly fails. Proper warning and error popups will be added in the future
- Probably some more things I'm forgetting

I decided to release this early version of ThimbleMonkey despite these lmitations and shortcomings, because some people want to be able to dig through the files, and no other programs are available yet that run on Windows, MacOS, and Linux.  
Secondly, I may not be able to work on this project for a while, and I didn't want it to linger uselessly on my harddrive during that time
