# ThimbleMonkey
A Python 3 / PySide6 graphical program to view game files from Thimbleweed Park, Delores, and Return To Monkey Island.  
This project is based very much on the work done over at [Dinky Explorer](https://github.com/bgbennyboy/Dinky-Explorer). Thanks!

## How to run
### From release
Just double-click the executable. Easy!
On the ARM version of MacOS (So M1, M2, and so on) you may have to run ThimbleMonkey through Rosetta. Select ThimbleMonkey in Finder, then open its Info screen by either pressing command + I, selecting 'File' and then 'Get Info', or right-clicking ThimbleMonkey and selecting 'Get Info'. Then check 'Open using Rosetta', close the Info window, and run ThimbleMonkey.

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
- In the commandprompt or terminal, run the command 'python -m venv --system-site-packages venv'. This creates the virtual environment
- Activate the virtual environment by typing 'venv\Scripts\activate' on Windows or 'source venv/bin/activate' on Linux and MacOS
- Run the command 'python -m pip install --upgrade pip' to make sure the latest pip version is used
- Run the command 'python -m pip install -r requirements.txt' to install the required libraries in your new virtual environment
- Now you're done with the setup! Move on to 'Starting ThimbleMonkey'
#### Updating
(**Note**: On MacOS and some Linux flavors, use 'python3' instead of 'python' for these steps)
- Download the code the same way as in the 'Initial Setup' section, overwriting the existing code
- Activate the virtual environment by typing 'venv\Scripts\activate' on Windows or 'source venv/bin/activate' on Linux and MacOS
- Run the command 'python -m pip install --upgrade pip' to make sure the latest pip version is used
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
First you need to know where the game files are stored.  
You can find this location in Steam by right-clicking one of the supported games, selecting 'Manage' and then 'Browse Local Files'.  
Once you know the location, there's two ways to load the game files:
#### Through the File menu:
- Click 'File' and select 'Load game folder...'. This opens up a file browser
- Navigate to where your Thimbleweed Park, Delores, and/or Return To Monkey Island game files are. No files show up in the file browser, because you're selecting a whole folder
- Click 'Select folder'
#### Drag & Drop:
- Drag the game folder onto ThimbleMonkey

Either method makes ThimbleMonkey load all the ggpack files from the game folder. This could take a little while.  
The list on the left should have filled with a lot of filenames now. Double-click one to see the file contents on the right.  
Some interesting file types: '.ktxbz' file are images, '.otf' and '.ttf' files are fonts, '.yack' files are conversation script files, and '.assets.bank' files contain sounds and music. But I'm sure every file has something interesting in it

### Filtering the file list
On the bottom left, there is a 'Filter' textbox. Type a filename filter in here and press Enter or click the search button next to it, and the file list will be filtered on the entered text.  
This filtering supports wildcards: '?' for a single character, '\*' for multiple characters. Examples: 'Banner_?-hd.ktxbz' lists all the Banner image files, '\*.ktxbz' lists all the image files

### Closing tabs
You can open multiple files. They open in separate tabs.  
Because images (files ending in '.ktxbz' or '.png') and soundbanks (file ending in '.assets.bank') can take up quite a bit of memory, you can easily close a single tab by clicking the 'X' on the right of the tab bar. The 'Tabs' menu contains options to close multiple tabs at once.

### Saving data
There are two types of saving in ThimbleMonkey: saving data as-is, and saving converted data.  
Saving data as-is is done by going to the 'File' menu and selecting 'Save...'. Selecting any of these options saves the applicable file(s) just as they are stored in the game files. For instance, an RtMI image will be saved as a .ktxbz file  
Saving converted data is done by going to the 'File' menu and selecting 'Convert and save...'. Selecting any of these options saves the applicable file(s) in a way that other programs can read. For instance, an RtMI image will be saved as a PNG file  
The four options in either menu are:
- 'current tab': This saves the file from only the currently selected and opened file tab
- 'open tabs': This saves the files from all the currently opened tabs. If only one tab is opened, this does the same thing as the previous option
- 'filtered files': This saves all the files currently listed in the file list on the left. So if you typed '.ktxbz' into the filter field as described in 'Filtering the file list', this would save all the listed images. If no filter is set, this does the same thing as the next option, 'all files'
- 'all files': This saves all the files currently loaded, regardless of the filter

Converting and saving a lot of files at once can take a long time. As an example, converting and saving all the Return To Monkey Island files took 24 minutes on my computer, saving to an SSD.  
So if you're saving a lot of files, a warning will pop up asking if you're sure. This allows you to narrow your filter or open tabs, or to prepare for a long wait.

## Limitations
- The parsing of the main Delores and RtMI game script file, ending in '.dink', is not finished. The results kind of make sense, but since the parsing isn't complete, the result isn't always correct
- Parsing of the conversation files ('.yack') isn't fully finished yet, but it's already readable
- Viewing text and images is slightly clumsy right now. More view controls will be added in the future
- Some actions take a while, especially opening '.assets.bank' files, which freezes the whole window. A progress bar for these actions will probably be added in the future
- Probably some more things I'm forgetting

I hope ThimbleMonkey can be useful and/or fun to you!
