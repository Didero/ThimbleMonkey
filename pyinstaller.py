import os, shutil, time, zipfile

import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_dynamic_libs


if __name__ == '__main__':
	startTime = time.perf_counter()
	programName = 'ThimbleMonkey'

	pyInstallerArguments = [
		'main.py',
		'--name=' + programName,
		'--onefile',
		'--clean',  # Always start with a new cache
		'--noconfirm',  # Clean the 'dist' folder
		'--noconsole'
	]

	# PyOgg needs DLLs in particular places. Add those to the arguments list too
	pyOggBinaries = collect_dynamic_libs("pyogg")
	for dllSourcePath, dllTargetPath in pyOggBinaries:
		pyInstallerArguments.append(f'--add-binary={dllSourcePath}{os.pathsep}.')

	print("PyInstaller arguments:")
	print(pyInstallerArguments)
	PyInstaller.__main__.run(pyInstallerArguments)

	# Copy the license and readme over too
	for filename in ('LICENSE', 'readme.md'):
		print(f"Copying {filename} to dist")
		shutil.copy2(filename, 'dist')
	print("Copying readme.md to readme.txt")
	shutil.copy2('readme.md', os.path.join('dist', 'readme.txt'))

	# Check on which OS we're building by file extension, .exe is Windows, .app is MacOS, no extension is Linux (On MacOS a no-extension file is generated too, but we ignore that)
	for programFilename, osName in ((f'{programName}.exe', 'Windows'), (f'{programName}.app', 'MacOS'), (programName, 'Linux')):
		programFilepath = os.path.join('dist', programFilename)
		if os.path.exists(programFilepath):
			with zipfile.ZipFile(os.path.join('dist', f'{programName}_{osName}.zip'), 'w') as distZip:
				print(f"Creating distribution zipfile {distZip.filename}")
				for filename in ('LICENSE', 'readme.md', 'readme.txt', programFilename):
					filepath = os.path.join('dist', filename)
					print(f"Adding {filename} to distribution zipfile")
					distZip.write(filepath, filename)
			break
	else:
		print("Unable to determine OS, not creating a distribution zip")

	print(f"Build took {time.perf_counter() - startTime} seconds")
