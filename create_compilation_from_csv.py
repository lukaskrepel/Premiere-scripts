import pymiere
from pymiere import wrappers

import random
import time
import re

from pathlib import Path

import csv

import LK_pymiere # TODO implement this all over

# IMPORTANT!
# Premiere files should use this filename convention:
# "CP001_DinosaursHalloween_ABC01_v001_L.prproj"
# (compilation_code / tags_capilatized / first_episode_code / file_version / author_initial / extension)

# Constants
CLUB_BABOO_PATH = "Y:\\Club Baboo" # "/Volumes/megagamma_data/Club Baboo/"
ALLOWED_REPETITIVE_COUNT = 3
CLIP_FOLDER_NAME = "VOORCOMP_MP4"
AUDIO_FOLDER_NAME = "AUDIO"
SKETCH_MUSIC_ITEM_NAME = "Sketches_Score_EndlessLoop.wav"
INTRO_FOLDER_NAME = "INTRO_MP4"
OUTRO_FOLDER_NAME = "OUTRO_MP4"
SEQUENCES_FOLDER_NAME = "PREM_SEQS"
ALL_TAGS = "GenericAnimalsDinosaursVehiclesSongsHalloweenChristmasEasterNewyearDinorangers" # <-- When using CP001_ClubBaboo_etc it uses all tags.
MUSIC_PATH = "Y:\Club Baboo\Audio\music\Daan\Sketches_Score_EndlessLoop.wav"

TARGET_AGE = 0
TARGET_AGE_RANGE = 0 #"All" # "1-4" # Use this, only if TARGET_AGE is set to 0
TARGET_HOURS = 1
MAX_CONSECUTIVE_SKETCHES = 3 # Maximum number of consecutive sketches allowed

# premiere uses ticks as its base time unit, this is used to convert from ticks to seconds
TICKS_PER_SECONDS = 254016000000

# BACKUP OLD WEIGHTS
# Define the weights for each category
CATEGORY_WEIGHTS = {
	'DinoFacts': 0.5,
	'Sketches': 0.6,
	'MagicShow': 0.6,
	'Construction': 0.5,
	'DinoDayCare': 0.4,
	'BabyMatch': 0.3,
	'Bones': 0.2,
	'Alphabet': 0.2,
	'MysteryAnimals': 0.2,
	'BarnDoors': 0.2,
	'CarWash': 0.2,
	'AnimalSounds': 0.2,
	'Wrong Heads': 0.1,
	'Drawing and Coloring': 0.1,
	'Memory': 0.1,
	'Puzzle': 0.1,
	'Counting': 0.1,
	'Colors': 0.1
}
DEFAULT_WEIGHT = 0.1

# CATEGORY_WEIGHTS = {
# 	'DinoFacts': 0.5,
# 	'Sketches': 99,
# 	'MagicShow': 0.5,
# 	'Construction': 0.5,
# 	'DinoDayCare': 0,
# 	'BabyMatch': 0,
# 	'Bones': 0.5,
# 	'Alphabet': 0,
# 	'MysteryAnimals': 0.0,
# 	'BarnDoors': 0.0,
# 	'CarWash': 0.0,
# 	'AnimalSounds': 0.0,
# 	'Wrong Heads': 0.0,
# 	'Drawing and Coloring': 0.0,
# 	'Memory': 0.0,
# 	'Puzzle': 0.0,
# 	'Counting': 0.0,
# 	'Colors': 0.0
# }
# DEFAULT_WEIGHT = 0.1

# Define a mapping of categories to color labels
CATEGORY_COLOR_LABELS = {
	'DinoFacts': 1,
	'Sketches': 2,
	'MagicShow': 3,
	'Construction': 4,
	'DinoDayCare': 5,
	'BabyMatch': 6,
	'Bones': 7,
	'Alphabet': 8,
	'MysteryAnimals': 9,
	'BarnDoors': 10,
	'CarWash': 11,
	'AnimalSounds': 12,
	'Wrong Heads': 13,
	'Drawing and Coloring': 14,
	'Memory': 15,
	'Puzzle': 15,
	'Counting': 15,
	'Colors': 15
}

# Main function to execute the script
def main():
	print("---START---")
	if not LK_pymiere.is_premiere_ready():
		exit()
	project = LK_pymiere.get_project() # project = pymiere.objects.app.project
	qe_project = pymiere.objects.qe.project
	# Split by underscore (_) and extract the relevant part
	parts = project.name.split("_")
	compilation_code = parts[0]
	tags_string = parts[1] # "VehiclesDinosaurs"
	# --
	if tags_string == "ClubBaboo":
		tags_string = ALL_TAGS
	# --
	print("Split project name intro parts: " + project.name + " -> ")
	for part in parts:
		print(" - " + part)
	first_video_code = parts[2]
	# Add spaces before capital letters and split into tags
	tags = re.findall(r'[A-Z][a-z]*', tags_string) # Divide capitalized, for example "VehiclesDinosaurs" becomes [ "Vehicles", "Dinosaurs"]

	###
	# read csv file:
	videos = get_videos_from_csv(project)
	# if TARGET_AGE != 0:
	# 	videos = filter_videos_by_target_age(videos, TARGET_AGE)
	# else:
	# 	videos = filter_videos_by_target_age_range(videos, TARGET_AGE_RANGE)
	# playlist = create_playlist(videos)
	playlist = create_playlist(videos, first_video_code, 60*60*TARGET_HOURS)
	sequence = create_sequence_from_playlist(project, playlist)
	move_sketches_audio_down_a_layer(sequence)
	remove_temp_video_track(qe_project)
	insert_sketches_loop_music(project)
	add_transitions(qe_project)
	LK_pymiere.remove_empty_tracks(qe_project)
	LK_pymiere.set_in_out_point(project.activeSequence)
	LK_pymiere.send_sequence_to_media_encoder(project)
	LK_pymiere.save_and_close_project(project)
	#
	print("---FINISHED---")


def get_videos_from_csv(project):
	print("Getting videos from CSV...")
	# Read the CSV file and extract video information
	videos = []
	with open('voorcomp_data.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			codename = row['codename']
			category = row['category']
			filename = row['filename']
			mediapath = '' + CLUB_BABOO_PATH + "\\FINALS\\VoorComp\\" + category + '\\' + filename #TODO PATHLIB
			inpoint = float(row['inpoint'])
			outpoint = float(row['outpoint'])
			tags = row['tags']
			age_range = row['age_range']
			rating = row['rating']
			short_description = row['short_description']	
			long_description = row['long_description']
			video = Video(codename, category, filename, mediapath, inpoint, outpoint, tags, age_range, rating, short_description, long_description)
			videos.append(video)
	return videos

# Function to filter videos by target age range, which is a string
def filter_videos_by_target_age_range(videos, target_age_range=TARGET_AGE_RANGE):
	print("Filtering videos by target age range...")
	print(len(videos), "videos before filtering")
	filtered_videos = []
	for video in videos:
		if (video.age_range == target_age_range or video.age_range == "All"):
			filtered_videos.append(video)
	print(len(filtered_videos), "videos after filtering")
	return filtered_videos

# Function to filter videos by target age, which is a single integer
def filter_videos_by_target_age(videos, target_age_range=TARGET_AGE):
	print("Filtering videos by target age...")
	print(len(videos), "videos before filtering")
	filtered_videos = []
	for video in videos:
		# Parse the age_range string into min and max values
		try:
			min_age, max_age = map(int, video.age_range.split('-'))
			# Check if the target age falls within the range
			if min_age <= target_age_range <= max_age:
				filtered_videos.append(video)
			elif video.age_range == "All":
				filtered_videos.append(video)
		except ValueError:
			print(f"Invalid age range format for video: {video.codename} ({video.age_range})")
	print(len(filtered_videos), "videos after filtering")
	return filtered_videos

# Function to create a video playlist with weighted random selection
def create_playlist(videos, first_video_code="", target_duration=60*60*TARGET_HOURS):
	print("Creating playlist...")
	print("Target duration: " + str(target_duration))
	print(f"First video code: '{first_video_code}'")
	playlist = []
	total_duration = 0
	previous_category = None
	consecutive_sketches = 0
	print("------")
	while videos and total_duration < target_duration:
		# Filter valid videos based on the previous category and sketch constraints
		valid_videos = [
			video for video in videos
			if (video.category != previous_category or video.category == "Sketches")
		]
		if len(playlist) == 3:
			valid_videos = [
				video for video in videos
				if (video.category == "Intro")
			]
		# Apply constraints for consecutive sketches
		elif previous_category == "Sketches" and consecutive_sketches < MAX_CONSECUTIVE_SKETCHES:
			valid_videos = [video for video in valid_videos if video.category == "Sketches" and video.category != "Intro" and video.category != "Outro"]
		elif previous_category == "Sketches" and consecutive_sketches >= MAX_CONSECUTIVE_SKETCHES:
			valid_videos = [video for video in valid_videos if video.category != "Sketches" and video.category != "Intro" and video.category != "Outro"]
		if not valid_videos:
			break
		# Get the weights for the valid videos, using the default weight if the category is not defined
		weights = [
			CATEGORY_WEIGHTS.get(video.category, DEFAULT_WEIGHT) + (99999 if first_video_code in video.codename else 0)
			for video in valid_videos
		]
		next_video = random.choices(valid_videos, weights=weights, k=1)[0]
		print(f"{time.strftime('%H:%M:%S', time.gmtime(total_duration))} {next_video.short_description} ({next_video.codename})")
		playlist.append(next_video)
		videos.remove(next_video)
		total_duration += next_video.duration
		# Update the consecutive sketches counter
		if next_video.category == "Sketches":
			consecutive_sketches += 1
		else:
			consecutive_sketches = 0
		previous_category = next_video.category
	print("------")
	# add outro
	outro = [video for video in videos if video.category == "Outro"]
	if outro:
		outro_video = outro[0]
		print(f"Adding outro: {outro_video.codename}")
		playlist.append(outro_video)
		videos.remove(outro_video)
		total_duration += outro_video.duration
	print("- Playlist duration: " + time.strftime('%H:%M:%S', time.gmtime(total_duration)))
	return playlist

def create_sequence_from_playlist(project, playlist):
	# import media into Premiere
	imported_items = []
	voorcomp_bin = project.rootItem.createBin("VOORCOMP_MP4")
	for video in playlist:
		print(f"Importing: {video.filename}")
		success = project.importFiles(  
			[video.mediapath], # can import a list of media  
			suppressUI=True,  
			targetBin=voorcomp_bin,  
			importAsNumberedStills=False  
		)  
		# find media we imported  
		items = project.rootItem.findItemsMatchingMediaPath(video.mediapath, ignoreSubclips=False)
		imported_item = items[0]
		imported_item.name = video.codename
		imported_item.setInPoint(str(video.inpoint * TICKS_PER_SECONDS), 4)
		imported_item.setOutPoint(str(video.outpoint * TICKS_PER_SECONDS), 4)
		imported_item.setScaleToFrameSize()
        # Set color label based on category
		color_label = CATEGORY_COLOR_LABELS.get(video.category, 0)  # Default to 0 (None) if category not found
		imported_item.setColorLabel(color_label)
		imported_items.append(imported_item)
	# Create a new sequence
	firstVideoCode = imported_items[0].name.split('_')[0]
	# Split by underscore (_) and extract the relevant part
	parts = project.name.split("_")
	compilation_code = parts[0]
	tags_string = parts[1] # "VehiclesDinosaurs"
	# Add spaces before capital letters and split into tags
	tags = re.findall(r'[A-Z][a-z]*', tags_string) # Divide capitalized, for example "VehiclesDinosaurs" becomes [ "Vehicles", "Dinosaurs"]
	sequence_name = f"{compilation_code}_{tags_string}_Compilation_{firstVideoCode}"
	sequence_bin = project.rootItem.createBin("PREM_SEQS")
	created_sequence = project.createNewSequenceFromClips(sequence_name, imported_items, sequence_bin)
	sequence_settings = created_sequence.getSettings()
	sequence_settings.videoFrameWidth = 1920
	sequence_settings.videoFrameHeight = 1080
	sequence_settings.videoDisplayFormat = 101 # 101 = 25 Timecode
	created_sequence.setSettings(sequence_settings) # Apply the settings to the sequence
	return created_sequence

def move_sketches_audio_down_a_layer(sequence):
	print("Moving sketches audio down a layer...")
	# get first video track of active sequence  
	track = sequence.audioTracks[0]
	newTrack = sequence.audioTracks[1]
	clips_to_adjust = []
	for i in range(track.clips.numItems):
		clip = track.clips[i]
		if "SK" in clip.name and not "SK03" in clip.name:
			clips_to_adjust.append(clip)
	for clip in clips_to_adjust:
		newTrack.insertClip(clip.projectItem, clip.start.seconds)
		clip.remove(False, False)

def remove_temp_video_track(qe_project):
	print("Removing temp video track...")
	qe_sequence = qe_project.getActiveSequence()
	qe_sequence.removeVideoTrack(1)

def insert_sketches_loop_music(project):
	print("Insert sketches loop music...")
	#music_item = get_music(project)
	music_item = import_item(project, MUSIC_PATH)
	print("- Music_item: " + music_item.name)
	sequence = project.activeSequence
	video_track = sequence.videoTracks[0]
	music_track = sequence.audioTracks[0]
	in_points = []
	out_points = []
	for i in range(video_track.clips.numItems):
		clip = video_track.clips[i]
		if "SK" in clip.name and not "SK03" in clip.name:
			start = clip.start.ticks
			end = start + clip.duration.ticks
			in_points.append(start)
			out_points.append(end)
	# Find common elements
	common_elements = set(in_points) & set(out_points)
	# Remove common elements from both lists
	in_points = [item for item in in_points if item not in common_elements]
	out_points = [item for item in out_points if item not in common_elements]
	# Iterate through both lists
	for in_point, out_point in zip(in_points, out_points):
		#print(f"In: {in_point} - Out: {out_point}")
		duration = (out_point - in_point) / TICKS_PER_SECONDS
		music_item.setInPoint(0, 2) # 2 = Audio only
		music_item.setOutPoint(duration, 2) # 2 = Audio only
		music_track.insertClip(music_item, in_point / TICKS_PER_SECONDS)


def add_transitions(qe_project):
	print("Adding transitions...")
	# Get active sequence and relevant tracks
	qe_sequence = qe_project.getActiveSequence()
	qe_video_tracks = [qe_sequence.getVideoTrackAt(0)]
	qe_audio_tracks = [qe_sequence.getAudioTrackAt(0), qe_sequence.getAudioTrackAt(1)]
	# Helper function to add transitions
	def add_transition(track, transition_type, time_code):
		print(f"Adding {transition_type} transitions...")
		transition_function = qe_project.getVideoTransitionByName if transition_type == "video" else qe_project.getAudioTransitionByName
		transition_name = "Cross Dissolve" if transition_type == "video" else "Exponential Fade"
		transition_to_apply = transition_function(transition_name)
		num_items_offset = -2 if transition_type == "video" else -1
		for j in range(track.numItems + num_items_offset):
			item = track.getItemAt(j)
			item.addTransition(transition_to_apply, False, time_code)
	# Add transitions to video and audio tracks
	for qe_video_track in qe_video_tracks:
		add_transition(qe_video_track, "video", '00;00;01;00')
	for qe_audio_track in qe_audio_tracks:
		add_transition(qe_audio_track, "audio", '00;00;01;00')


# Video class to store video metadata
class Video:
	def __init__(self, codename, category, filename, mediapath, inpoint, outpoint, tags, age_range, rating, short_description, long_description):
		self.codename = codename
		self.category = category
		self.filename = filename
		self.mediapath = mediapath
		self.inpoint = inpoint
		self.outpoint = outpoint
		self.duration = outpoint - inpoint
		self.tags = tags
		self.age_range = age_range
		self.rating = rating
		self.short_description = short_description
		self.long_description = long_description
	def __repr__(self):
		return f"{self.codename}"

def import_item(project, mediapath):
	print(f"Importing item: {mediapath}")
	success = project.importFiles(  
		[mediapath], # can import a list of media  
		suppressUI=True,
		targetBin=project.rootItem, 
		importAsNumberedStills=False  
	)  
	# find media we imported  
	items = project.rootItem.findItemsMatchingMediaPath(mediapath, ignoreSubclips=False)
	imported_item = items[0]
	return imported_item

# Run main function
main()