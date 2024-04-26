import pathlib
import pymiere
from pymiere.wrappers import time_from_seconds
from array import array

ServerFolderName = "Renders"
PremBinName = "RENDERS"
PotentialPremBinNames = ["renders", "shotrenders", "mohorenders"]


def main():
	print("---START---")
	if not is_premiere_ready():
		exit()
	project = pymiere.objects.app.project # get premiere project
	renders_bin = select_bin(project)
	# Split the path into parts based on '/'
	path_parts = project.path.split('/')
	# Construct the new path by joining the necessary parts
	rendersPath = '/'.join(path_parts[:-2]) + '/' + ServerFolderName
	files = get_first_files(rendersPath)
	import_as_image_sequences(project, renders_bin, files)
	rename_items(project)
	print("---FINISHED---")


def select_bin(project):
	print("Finding Renders bin...")
	found_bin = False
	for i in range (0, project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		for name in PotentialPremBinNames:
			lowercase = item.name.lower()
			print ("LOWER" + lowercase)
			if lowercase == name:
				item.renameBin(PremBinName)
		if item.name == PremBinName:
			found_bin = True
			return item
	if not found_bin:
		project.rootItem.createBin(PremBinName)
		return select_bin(project)


def rename_items(project):
	print("Renaming...")
	for i in range (0, project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == "Renders":
			for j in range (0, item.children.numItems):
				childItem = item.children[j]
				#print("Child item: " + childItem.name)
				name = childItem.name
				#input_string = "DF06_032_KeraWhut_00001.png"
				first_underscore_index = name.find('_')  # Find the index of the first underscore
				last_underscore_index = name.rfind('_')  # Find the index of the last underscore
				if first_underscore_index < last_underscore_index:
					desired_name = name[first_underscore_index + 1:last_underscore_index]  # Extract the desired substring
					childItem.name = desired_name
	project.consolidateDuplicates()


def get_first_files(directory):
	print("Finding image sequence paths...")
	"""
	Get the first file (alphabetically sorted) from each subdirectory.
	
	Args:
	- directory: Path to the directory.
	
	Returns:
	- List of paths to the first file from each subdirectory.
	"""
	first_files = []
	path = pathlib.Path(directory)
	for item in path.iterdir():
		if item.is_dir():
			sub_files = list(item.glob('*'))
			if sub_files:
				first_files.append(str(min(sub_files)))
	# Sort list alphabetically
	first_files.sort()
	return first_files


def is_premiere_ready():
	print("Finding Premiere...")
	# Print if premiere doc is opened
	isReady = pymiere.objects.app.isDocumentOpen()
	if isReady:
		print ('Premiere project is open.')
	else:
		print ('WARNING: No open Premiere project found!')
	return isReady


def import_as_image_sequences(project, bin, filePaths):
	print("Importing image sequences...")
	for file in filePaths:
		print("Importing " + file)
		this_file = [] # Array with a single file, because we want to import it as an image sequence.
		this_file.append(file)
		bin.select()
		success = project.importFiles(
			this_file, # can import a list of media (Not if importAsNumberedStills == True!)
			suppressUI=True,  
			targetBin=project.getInsertionBin(),  
			importAsNumberedStills=True
		)


# Run main function
main()