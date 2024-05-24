import pymiere
from pymiere import wrappers
from pymiere.wrappers import timecode_from_seconds
from pymiere.wrappers import get_item_recursive
from pymiere.wrappers import move_clip
from pymiere.wrappers import time_from_seconds
import random
import time

# Constants
ALLOWED_REPETITIVE_COUNT = 3
CLIP_FOLDER = "VOORCOMP_MP4"
AUDIO_FOLDER = "AUDIO"
SKETCH_MUSIC = "Sketches_Score_EndlessLoop.wav"

# premiere uses ticks as its base time unit, this is used to convert from ticks to seconds
TICKS_PER_SECONDS = 254016000000

# Define the weights for each category
CATEGORY_WEIGHTS = {
	'DinoFacts': 1,
	'Sketches': 0.6,
	'Construction': 0.5,
	'DinoDayCare': 0.4,
	'BabyMatch': 0.3,
	'Bones': 0.2,
	'ABC': 0.2,
	'WrongHeads': 1
}
DEFAULT_WEIGHT = 0.1

# Main function to execute the script
def main():
	print("---START---")
	project = pymiere.objects.app.project
	qe_project = pymiere.objects.qe.project
	videos = get_videos(project)
	playlist = create_video_playlist(videos)
	create_sequence(project, playlist)
	move_sketches_audio_down_a_layer(project.activeSequence)
	remove_temp_video_track(qe_project)
	insert_sketches_loop_music(project)
	remove_empty_tracks(qe_project)
	print("---FINISHED---")

# Video class to store video metadata
class Video:
	def __init__(self, filename, duration, category, projectItem):
		self.filename = filename
		self.duration = duration
		self.category = category
		self.projectItem = projectItem
	def __repr__(self):
		return f"{self.filename} ({time.strftime('%H:%M:%S', time.gmtime(self.duration))} min, {self.category})"

def get_music(project):
	print("Getting music...") #TODO fix this code cleanup
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == AUDIO_FOLDER:
			for j in range(item.children.numItems):
				child_item = item.children[j]
				if child_item.name == SKETCH_MUSIC:
					return child_item

# Function to get all videos from the project
def get_videos(project):
	print("Getting videos...")
	videos = []
	categories = set()
	for i in range(project.rootItem.children.numItems):
		item = project.rootItem.children[i]
		if item.name == CLIP_FOLDER:
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
def create_video_playlist(videos, target_duration=60*60):
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
		weights = [CATEGORY_WEIGHTS.get(video.category, DEFAULT_WEIGHT) for video in valid_videos]
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
	music_item = get_music(project)
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
		print(f"In: {in_point} - Out: {out_point}")
		duration = (out_point - in_point) / TICKS_PER_SECONDS
		music_item.setInPoint(0, 2) # 2 = Audio only
		music_item.setOutPoint(duration, 2) # 2 = Audio only
		music_track.insertClip(music_item, in_point / TICKS_PER_SECONDS)

def remove_empty_tracks(qe_project):
	print("Removing empty tracks from sequence...")
	qe_sequence = qe_project.getActiveSequence()
	qe_sequence.removeEmptyVideoTracks()
	qe_sequence.removeEmptyAudioTracks()

# Run main function
main()
