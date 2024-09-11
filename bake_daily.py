import pymiere
from pymiere import wrappers
import time
import re
import datetime
import os

# Constants
# premiere uses ticks as its base time unit, this is used to convert from ticks to seconds
TICKS_PER_SECONDS = 254016000000
EXTENSION = "mp4"
# Mapping of month numbers to Dutch abbreviations
DUTCH_MONTHS = {
    1: "jan",
    2: "feb",
    3: "mrt",
    4: "apr",
    5: "mei",
    6: "jun",
    7: "jul",
    8: "aug",
    9: "sept",
    10: "okt",
    11: "nov",
    12: "dec"
}

# Main function to execute the script
def main():
	print("---START---")
	project = pymiere.objects.app.project
	set_in_out_point(project.activeSequence)
	unmute_all_audio(project.activeSequence)
	send_sequence_to_media_encoder(project)
	print("---FINISHED---")

# Set the in and out point for a sequence to the entire sequence
def set_in_out_point(sequence):
	print("Setting in/out points for sequence...")
	sequence.setInPoint(0)
	sequence.setOutPoint(sequence.end)

# Unmute audio layers in the entire sequence
def unmute_all_audio(sequence):
	print("Unmuting all audio for sequence...")
	for audioTrack in sequence.audioTracks:
		audioTrack.setMute(0) # If 1, mute the track. If 0, the track will be unmuted.

def send_sequence_to_media_encoder(project):
	print("Sending sequence to Adobe Media Encoder...")
	output_path = project.path
	output_path = output_path.replace("Edit", "Dailies")
	pattern = r'_v\d+_.+\..+$' #pattern = r'_([^_]+)_v\d+_.+\..+$'
	output_start = re.sub(pattern, "", output_path) # removes '_v001_L.prproj'
	# Get today's date
	today = datetime.date.today()
	daystamp = f"{today.day}{DUTCH_MONTHS[today.month]}"
	# create output path
	output_path = f"{output_start}_{daystamp}.{EXTENSION}"
	# Check if the file already exists, and if it does, increment the counter
	counter = 1
	while os.path.exists(output_path):
		counter += 1
		output_path = f"{output_start}_{daystamp}_{counter}.{EXTENSION}"
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

# Run main function
main()