import pymiere
import xml.etree.ElementTree as ET  # For parsing the XML metadata
from pathlib import Path

AUDIO_FOLDER_NAME = "AUDIO"
RENDERS_FOLDER_NAME = "RENDERS"
TRASH_FOLDER_NAME = "TRASH"

def is_premiere_ready():
	print("Checking if Premiere is ready...")
	# Print if premiere doc is opened
	is_ready = pymiere.objects.app.isDocumentOpen()
	if is_ready:
		print('- Premiere project is open.')
	else:
		print('- WARNING: No open Premiere project found!')
	return is_ready

def consolidate_duplicates(project):
	print("Consolidating duplicates...")
	project.consolidateDuplicates()

def remove_unused(project):
	print("Removing unused items...")
	trash_bin = get_or_create_trash_bin(project)
	all_items = get_all_project_items(project)
	# Iterate over all project items and delete unused ones
	for item in all_items:
		if not item.isSequence():
			if not is_item_used(item):
				print(f"Moving unused item: {item.name} to {AUDIO_FOLDER_NAME}")
				item.moveBin(trash_bin)
	delete_empty_bins(project)

# Function to get or create a "TRASH" bin
def get_or_create_trash_bin(project):
	root = project.rootItem
	# Check if the "TRASH" bin already exists
	for child in root.children:
		if child.name == TRASH_FOLDER_NAME and child.type == 2:  # Type 2 means bin
			return child
	# If not, create a new "TRASH" bin
	new_bin = root.createBin(TRASH_FOLDER_NAME)
	return new_bin

def delete_empty_bins(project):
	print("Deleting empty bins")
	trash_bin = get_or_create_trash_bin(project)
	project = pymiere.objects.app.project
	all_bins = get_all_project_bins(project)
	# Iterate over all project items and delete unused ones
	for item in all_bins:
		if item.children.numItems == 0:
			print(f"Moving empty bin: {item.name} to Trash")
			item.moveBin(trash_bin)

# Function to get all items in the project, starting from the root
def get_all_project_items():
	return get_child_items(project.rootItem)

# Function to check if a project item is used (via VideoUsage and AudioUsage)
def is_item_used(item):
	metadata_xml = item.getProjectMetadata()
	# Parse the metadata XML string
	root = ET.fromstring(metadata_xml)
	namespaces = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
				  'premiere': 'http://ns.adobe.com/premierePrivateProjectMetaData/1.0/'}
	# Extract AudioUsage and VideoUsage from the metadata
	audio_usage = root.find('.//premiere:Column.Intrinsic.AudioUsage', namespaces)
	video_usage = root.find('.//premiere:Column.Intrinsic.VideoUsage', namespaces)
	# Convert the values to integers if they exist
	audio_usage_value = int(audio_usage.text) if audio_usage is not None else 0
	video_usage_value = int(video_usage.text) if video_usage is not None else 0
	# The item is used if either audio or video usage is greater than 0
	return audio_usage_value > 0 or video_usage_value > 0

# Function to get all child items of a bin, including recursively nested ones
def get_child_items(bin_item):
	items = []
	if hasattr(bin_item, 'children') and bin_item.children is not None:
		# If the item is a bin (has children), go deeper
		if bin_item.children.numItems > 0:
			for child in bin_item.children:
				items.extend(get_child_items(child))  # Recursively add children items
	else:
		items.append(bin_item)  # If it's a regular item, add it to the list
	return items

# Function to get all items in the project, starting from the root
def get_all_project_items(project):
	print("Getting all project items...")
	return get_child_items(project.rootItem)

def get_all_project_bins(project):
	print("Getting all project bins...")
	return get_child_bins(project.rootItem)

# Function to get all child bins of a bin, including recursively nested ones
def get_child_bins(bin_item):
	bins = []
	if hasattr(bin_item, 'children') and bin_item.children is not None:
		# If the item is a bin (has children), go deeper
		if bin_item.children.numItems > 0:
			for child in bin_item.children:
				if child.type == 2:  # Check if the child is a bin (type 2)
					bins.append(child)  # Add bin to the list
					bins.extend(get_child_bins(child))  # Recursively add child bins
	return bins

def consolidate_audio_bins(project):
	print("Consolidating audio bins...")
	# Get all bins in the project
	all_bins = get_all_project_bins(project)
	# Find the target bin (the one we will move content into)
	target_bin = None
	for bin_item in all_bins:
		if bin_item.name == AUDIO_FOLDER_NAME:
			target_bin = bin_item
			break
	if target_bin is None:
		print(f"No target '{AUDIO_FOLDER_NAME}' bin found. Creating one.")
		target_bin = project.rootItem.createBin(AUDIO_FOLDER_NAME)
	# Iterate over all bins and move items from matching bins into the target bin
	for bin_item in all_bins:
		if bin_item.name.lower() == "audio" and bin_item != target_bin:  # Check for case-insensitive match
			print(f"Moving items from bin: {bin_item.name} to bin: {target_bin.name}")
			#move_all_items(bin_item, target_bin)
			if bin_item.children.numItems > 0:
				for child in bin_item.children:
					print(f"Moving item: {child.name} to {target_bin.name}")
					child.moveBin(target_bin)
	move_root_wav_files_to_audio_bin(project, target_bin)
	move_audio_only_folders_to_audio_bin(project, target_bin)
	print("Consolidation complete.")

def move_audio_only_folders_to_audio_bin(project, target_bin):
    print("Checking for folders with only audio files...")
    all_bins = get_all_project_bins(project)

    for bin_item in all_bins:
        # Only check bins, not individual items
        if bin_item.type == 2:  # Check if the item is a bin (type 2)
            audio_only = True
            for child in bin_item.children:
                # Check if each child is an audio file
                if child.type != 1:  # Check if the child is not a media item (type 1)
                    audio_only = False
                    break
                extension = Path(child.getMediaPath()).suffix.lower()
                if extension not in [".wav", ".mp3"]:
                    audio_only = False
                    break

            if audio_only:
                print(f"Moving audio-only folder: {bin_item.name} to {target_bin.name}")
                bin_item.moveBin(target_bin)

def move_root_wav_files_to_audio_bin(project, target_bin):
	if project.rootItem.children.numItems > 0:
		for item in project.rootItem.children:
			extension = Path(item.getMediaPath()).suffix.lower()
			if extension == ".wav" or extension == ".mp3":
				print(f"Moving item: {item.name} to {target_bin.name}")
				item.moveBin(target_bin)	

def get_project():
	print("Getting 'project'...")
	return pymiere.objects.app.project  # get premiere project