# ThimbleMonkey
A Python 3 / PySide6 graphical program to view game files from Thimbleweed Park, Delores, and Return To Monkey Island.  
This project is based very much on the work done over at [Dinky Explorer](https://github.com/bgbennyboy/Dinky-Explorer). Thanks!

## How to run
### From release
Just double-click the executable. Easy!

### From Python scripts
#### Initial setup
This project needs some libraries, so you probably want to set up a virtual environment first, to keep these libraries out of your main Python install.
There are some guides on the internet on how to do that, but briefly:  
(**Note**: On MacOS and some Linux flavors, use 'python3' instead of 'python' for these steps)
- Make sure you have Python installed. Try opening a commandprompt or terminal, and typing 'python --version'. You should get a version number. If you get an error, install Python 3
- Download this project from its GitHub page by clicking the green 'Code' button and selecting 'Download ZIP'. Or use a GIT client to check out the repository
- Extract the download ZIP somewhere, and open a commandprompt or terminal there
- Some extra Python modules are needed, depending on your operating system (if you're not sure, skip this step for now, and if the next step gives errors, return to this step and then try again):
  - For Windows, some specific DLLs are needed to open the .assets.bank sound files. [Download this ZIP](https://www.dropbox.com/s/uu4qywc07tim2pp/ThimbleMonkeyWindowsDLLs.zip?dl=0), and extract the DLLs into the ThimbleMonkey folder
  - For Linux:
    - Run the command 'sudo apt install python3-pip' and answer 'Y' when it asks you if you're sure you want to install.
    - Now we need to know which Python version is installed, so run 'python --version', and remember the output (for instance 'Python 3.10.6')
    - Run the command 'sudo apt install [python version]-venv', replacing '[python-version]' with the version you found in the previous step (for instance 'sudo apt install python3.10-venv'), again answering 'Y' when it asks if you're sure
    - Run the command 'sudo apt install git', again answering 'Y' if it asks for confirmation. We need git because one of the needed libraries comes from a git source
    - For sound playback support, we need some header files. Run the command 'sudo apt install libasound2-dev'
  - For MacOS:
    - Install Homebrew if it's not installed already. See [its homepage](https://brew.sh) for how to do that
    - Run the command 'brew install libogg'
    - Run the command 'brew install libvorbis'
- In the commandprompt or terminal, run the command 'python -m venv --system-site-packages venv'. This creates the virtual environment (If you get an error that 'pip' can't be found, run 'sudo apt-get install python-pip' or 'sudo apt-get install python3-pip' first)
- Activate the virtual environment by typing 'venv\Scripts\activate' on Windows or 'source venv/bin/activate' on Linux and MacOS
- Run the command 'python -m pip install -r requirements.txt' to install the required libraries in your new virtual environment
- If you want to be able to play the sounds and music, some further actions are needed. If you don't care about the music, skip to the 'Starting ThimbleMonkey' section
  - For Windows: Download [this library release](https://github.com/HearthSim/python-fsb5/releases/tag/b7bf605), and place the 'libogg.dll' and 'libvorbis.dll' files from the downloaded zip in the same folder as where you placed ThimbleMonkey
  - For Mac: Install 'libogg' and 'libvorbis'. If you have Homebrew installed, you can do so with the commands 'brew install libogg' and 'brew install libvorbis'
  - For Linux: Install 'libogg' and 'libvorbis' with the command 'sudo apt-get install libogg libvorbis'
- Now you're done with the setup! Move on to 'Starting ThimbleMonkey'
#### Updating
(**Note**: On MacOS and some Linux flavors, use 'python3' instead of 'python' for these steps)
- Download the code the same way as in the 'Initial Setup' section, overwriting the existing code
- Activate the virtual environment by typing 'venv\Scripts\activate' on Windows or 'source venv/bin/activate' on Linux and MacOS
- Since the updated code might have new or updated libraries, we need to install those, with the command 'python -m pip install --upgrade -r requirements.txt'
- Update done! Now you can start ThimbleMonkey as described in 'Starting ThimbleMonkey' below
#### Starting ThimbleMonkey
(**Note**: On MacOS and some Linux flavors, use 'python3' instead of 'python' for these steps)
- Open a commandprompt or terminal, and navigate to where you extracted ThimbleMonkey
- If you didn't just do the initial setup listed above, activate the virtual environment by typing 'venv\Scripts\activate' on Windows or 'source venv/bin/activate' on Linux and MacOS
- Run the command 'python -m main.py' or 'python -m main'
- ThimbleMonkey should start now

## Using ThimbleMonkey
### Loading game files
- Click 'File' and select 'Load game folder...'. This opens up a file browser
- Navigate to where your Return To Monkey Island game files are. You can find this location by opening Steam, right-clicking one of the supported games, and selecting 'Manage' and then 'Browse Local Files'. No files show up in the file browser, because you're selecting a whole folder. (Note that for Thimbleweed Park, you need to select the 'Resources' subfolder)
- Click 'Select folder'. This makes ThimbleMonkey load all the ggpack files from the game folder. This could take a little while
- The list on the left should have filled with a lot of filenames now. Double-click one to see the file contents on the right
- Some interesting file types: '.ktxbz' file are images, '.otf' and '.ttf' files are fonts, '.yack' files are conversation script files, and '.assets.bank' files contain sounds and music. But I'm sure every file has something interesting in it

### Filtering the file list
On the bottom left, there is a 'Filter' textbox. Type a filename filter in here and press Enter or click the search button next to it, and the file list will be filtered on the entered text.  
This filtering supports wildcards: '?' for a single character, '\*' for multiple characters. Examples: 'Banner_?-hd.ktxbz' lists all the Banner image files, '\*.ktxbz' lists all the image files

### Closing tabs
You can open multiple files. They open in separate tabs.  
Because images (files ending in '.ktxbz' or '.png') and soundbanks (file ending in '.assets.bank') can take up quite a bit of memory, you can easily close a single tab by clicking the 'X' on the right of the tab bar. The 'Tabs' menu contains options to close multiple tabs at once.

### Saving data
You can get files out of ThimbleMonkey in two ways:
- By clicking the 'File' menu and selecting 'Save current tab data', you can save the data from the current tab just as it is stored in the game files. An image will be saved as a .ktxbz file, for instance
- By clicking the 'File' menu and selecting 'Convert and save current tab data', you can save the data from the current tab in a way that other programs can read. An image will be saved as a PNG file, for instance
- (Sidenote: '.assets.bank' files contain music files, these can be saved in bulk as described in the previous entry, or individually by opening one of the soundfiles and clicking the 'Save' button)

## Limitations
- The parsing of the main Delores and RtMI game script file, ending in '.dink', is not finished. The results kind of make sense, but since the parsing isn't complete, the result isn't always correct
- Parsing of the conversation files ('.yack') isn't fully finished yet, but it's already readable
- Viewing text and images is slightly clumsy right now. More view controls will be added in the future
- Some actions take a while, especially opening '.assets.bank' files, which freezes the whole window. A progress bar for these actions will probably be added in the future
- Probably some more things I'm forgetting

I hope ThimbleMonkey can be useful and/or fun to you!
