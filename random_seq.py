import pymiere
from pymiere import wrappers
from pymiere.wrappers import timecode_from_seconds
from pymiere.wrappers import get_item_recursive
from pymiere.wrappers import move_clip
from pymiere.wrappers import time_from_seconds
import random
import time
import re

# Constants
ALLOWED_REPETITIVE_COUNT = 3
CLIP_FOLDER_NAME = "VOORCOMP_MP4"
AUDIO_FOLDER_NAME = "AUDIO"
SKETCH_MUSIC_ITEM_NAME = "Sketches_Score_EndlessLoop.wav"
INTRO_ITEM_NAME = "INTRO"
OUTRO_ITEM_NAME = "OUTRO"
BUMPERS_FOLDER_NAME = "BUMPERS & WIPES"
SEQUENCES_FOLDER_NAME = "PREM_SEQS"

# premiere uses ticks as its base time unit, this is used to convert from ticks to seconds
TICKS_PER_SECONDS = 254016000000

# Define the weights for each category
CATEGORY_WEIGHTS = {
	'DinoFacts': 1,
	'Sketches': 0.6,
	'MagicShow': 0.6,
	'Construction': 0.5,
	'DinoDayCare': 0.4,
	'BabyMatch': 0.3,
	'Bones': 0.2,
	'ABC': 0.2,
	'MysteryAnimals': 0.2,
	'BarnDoors': 0.2,
	'WrongHeads': 0.1,
	'Drawing and Coloring': 0.1,
	'Memory': 0.1,
	'Puzzle': 0.1,
	'Counting': 0.1
}
DEFAULT_WEIGHT = 0.1

# Main function to execute the script
def main():
	print("---START---")
	project = pymiere.objects.app.project
	qe_project = pymiere.objects.qe.project
	first_video_code = extract_first_video_code(project.name)
	videos = get_videos(project)
	playlist = create_video_playlist(videos, first_video_code)
	intro_item = find_item_in_folder(project, BUMPERS_FOLDER_NAME, INTRO_ITEM_NAME)
	playlist = add_to_playlist(playlist, intro_item, 3)
	outro_item = find_item_in_folder(project, BUMPERS_FOLDER_NAME, OUTRO_ITEM_NAME)
	playlist = add_to_playlist(playlist, outro_item, len(playlist))
	create_sequence(project, playlist)
	move_sketches_audio_down_a_layer(project.activeSequence)
	remove_temp_video_track(qe_project)
	insert_sketches_loop_music(project)
	add_transitions(qe_project)
	remove_empty_tracks(qe_project)
	set_in_out_point(project.activeSequence)
	send_sequence_to_media_encoder(project)
	save_and_close_project(project)
	print("---FINISHED---")

def add_to_playlist(playlist, item, pos):
	duration = (item.getOutPoint(1).seconds - item.getInPoint(1).seconds)
	intro = Video(item.name, duration, "Intro", item) #???
	playlist.insert(pos, intro)
	return playlist

# Video class to store video metadata
class Video:
	def __init__(self, filename, duration, category, projectItem):
		self.filename = filename
		self.duration = duration
		self.category = category
		self.projectItem = projectItem
	def __repr__(self):
		return f"{self.filename} ({time.strftime('%H:%M:%S', time.gmtime(self.duration))} min, {self.category})"

def extract_first_video_code(filename):
	# Define the regular expression pattern
	pattern = r'_([^_]+)_v\d+_.+\..+$'
	# Search for the pattern in the filename
	match = re.search(pattern, filename)
	# If a match is found, return the captured group
	if match:
		first_video_code = match.group(1)
		print("First Video Code: " + first_video_code)
		return first_video_code
	else:
		return "no code found"

def find_item_in_folder(project, folder_name, file_name):
	print("Getting file...")
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == folder_name:
			for j in range(item.children.numItems):
				child_item = item.children[j]
				if child_item.name == file_name:
					return child_item
	return None

def find_item(item, item_name):
	#print(f"Searching item {item_name}...")
	if item.name == item_name:
		return item
	#print(item.type)
	if item.type == 2 or item.type == 3: # (2 = BIN, 3 = ROOTITEM)
		for i in range(item.children.numItems):
			found_item = find_item(item.children[i], item_name)
			if found_item:
				return found_item
	return None

# Function to get all videos from the project
def get_videos(project):
	print("Getting videos...")
	videos = []
	categories = set()
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == CLIP_FOLDER_NAME:
			for j in range(item.children.numItems):
				childItem = item.children[j]
				category = childItem.name
				categories.add(category)  # Add category to the set
				print("Category: " + category)
				for k in range(childItem.children.numItems):
					grandChildItem = childItem.children[k]
					grandChildItem.setScaleToFrameSize()
					duration = (grandChildItem.getOutPoint(1).seconds - grandChildItem.getInPoint(1).seconds)
					videos.append(Video(grandChildItem.name, duration, category, grandChildItem))
	print(f"Found {len(videos)} videos in {len(categories)} categories.")
	return videos


# Function to create a video playlist with weighted random selection
def create_video_playlist(videos, first_video_code="", target_duration=60*60):
	print("Creating playlist...")
	playlist = []
	total_duration = 0
	previous_category = None
	consecutive_sketches = 0
	while videos and total_duration < target_duration:
		# Filter valid videos based on the previous category and sketch constraints
		valid_videos = [
			video for video in videos
			if (video.category != previous_category or video.category == "Sketches")
		]
		# Apply constraints for consecutive sketches
		if previous_category == "Sketches" and consecutive_sketches < 3:
			valid_videos = [video for video in valid_videos if video.category == "Sketches"]
		elif previous_category == "Sketches" and consecutive_sketches >= 3:
			valid_videos = [video for video in valid_videos if video.category != "Sketches"]
		if not valid_videos:
			break
		# Get the weights for the valid videos, using the default weight if the category is not defined
		weights = [
			CATEGORY_WEIGHTS.get(video.category, DEFAULT_WEIGHT) + (99999 if first_video_code in video.filename else 0)
			for video in valid_videos
		]
		next_video = random.choices(valid_videos, weights=weights, k=1)[0]
		playlist.append(next_video)
		videos.remove(next_video)
		total_duration += next_video.duration
		# Update the consecutive sketches counter
		if next_video.category == "Sketches":
			consecutive_sketches += 1
		else:
			consecutive_sketches = 0
		previous_category = next_video.category
	print("Playlist duration: " + time.strftime('%H:%M:%S', time.gmtime(total_duration)))
	return playlist

def create_sequence(project, playlist):
	# Create a new sequence
	firstVideoCode = playlist[0].filename.split('_')[0]
	compilationCode = project.name.split('_')[0]
	sequence_name = compilationCode + "_Dinosaurs_Compilation_" + firstVideoCode
	arrayOfProjectItems = []
	for video in playlist:
		arrayOfProjectItems.append(video.projectItem)
	print("Creating sequence: '" + sequence_name +"'")
	project.createNewSequenceFromClips(sequence_name, arrayOfProjectItems)
	# Move sequence item into bin
	bin_item = None
	seq_item = None
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == SEQUENCES_FOLDER_NAME:
			bin_item = item
		if item.name == sequence_name:
			seq_item = item
		if bin_item != None and seq_item != None:
			print("Moving new sequence into premiere bin...")
			seq_item.moveBin(bin_item)

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
	music_item = find_item_in_folder(project, AUDIO_FOLDER_NAME, SKETCH_MUSIC_ITEM_NAME)
	print("Music_item: " + music_item.name)
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

def remove_empty_tracks(qe_project):
	print("Removing empty tracks from sequence...")
	qe_sequence = qe_project.getActiveSequence()
	qe_sequence.removeEmptyVideoTracks()
	qe_sequence.removeEmptyAudioTracks()

def set_in_out_point(sequence):
	print("Setting in/out points for sequence...")
	sequence.setInPoint(0)
	sequence.setOutPoint(sequence.end)

def send_sequence_to_media_encoder(project):
	print("Sending sequence to Adobe Media Encoder...")
	output_path = project.path
	output_path = output_path.replace("Compilations", "FINALS")
	pattern = r'_v\d+_.+\..+$' #pattern = r'_([^_]+)_v\d+_.+\..+$'
	output_path = re.sub(pattern, ".mp4", output_path)
	preset_path = "/Applications/Adobe Media Encoder 2024/Adobe Media Encoder 2024.app/Contents/MediaIO/systempresets/4E49434B_48323634/YouTube 1080p HD.epr"
	print(f"Destination: {output_path}")
	print(f"Using preset: {preset_path}")
	# ensure Media Encoder is started
	pymiere.objects.app.encoder.launchEncoder()
	# add sequence to Media Encoder queue
	job_id = pymiere.objects.app.encoder.encodeSequence(
	    project.activeSequence,
	    output_path,  # path of the exported file
	    preset_path,  # path of the export preset file
	    pymiere.objects.app.encoder.ENCODE_IN_TO_OUT,  # what part of the sequence to export: ENCODE_ENTIRE / ENCODE_IN_TO_OUT / ENCODE_WORKAREA
	    removeOnCompletion=False,  # clear this job of media encoder render queue on completion
	    startQueueImmediately=False  # seem not to be working in Premiere 2017? Untested on versions above
	)
	# press green play button in the queue list to start encoding everything
	pymiere.objects.app.encoder.startBatch()

def save_and_close_project(project):
	print("Saving project...")
	project.save()
	print("Closing project...")
	project.closeDocument()

# Run main function
main()
