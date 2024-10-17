import pymiere
from pymiere import wrappers
import time
import re
import datetime
import os

# Constants
PRESET_PATH_FINAL = "/Volumes/megagamma_data/Club Baboo/Resources/AdobeMediaEncoder/Presets/YouTube 1080p HD.epr"
PRESET_PATH_MINIDAILY = "/Volumes/megagamma_data/Club Baboo/Resources/AdobeMediaEncoder/Presets/MiniDaily.epr"
TICKS_PER_SECONDS = 254016000000
EXTENSION = "mp4"
DUTCH_MONTHS = {1: "jan", 2: "feb", 3: "mrt", 4: "apr", 5: "mei", 6: "jun", 7: "jul", 8: "aug", 9: "sept", 10: "okt", 11: "nov", 12: "dec"}

# Main function to execute the script
def main():
    print("---START---")
    project = pymiere.objects.app.project

    if not project or not project.activeSequence:
        print("No active project or sequence found!")
        return

    sequence = project.activeSequence
    set_in_out_point(sequence)
    unmute_all_audio(sequence)

    # Send sequences to Adobe Media Encoder with different presets
    send_to_media_encoder(sequence, project, "MiniDaily", PRESET_PATH_MINIDAILY)
    send_to_media_encoder(sequence, project, "Final", PRESET_PATH_FINAL)

    # Start batch encoding
    pymiere.objects.app.encoder.startBatch()
    print("---FINISHED---")

# Set the in and out points for a sequence
def set_in_out_point(sequence):
    print("Setting in/out points for sequence...")
    sequence.setInPoint(0)
    sequence.setOutPoint(sequence.end)

# Unmute audio layers in the entire sequence
def unmute_all_audio(sequence):
    print("Unmuting all audio tracks...")
    for audioTrack in sequence.audioTracks:
        audioTrack.setMute(0)  # Unmute

# Create and validate output paths
def create_output_path(project_path, output_type, daystamp):
    output_path = project_path.replace("Edit", "Dailies")
    pattern = r'_v\d+_.+\..+$'
    output_start = re.sub(pattern, "", output_path)

    if output_type == "MiniDaily":
        return f"{output_start}_MiniDaily.{EXTENSION}"

    # Ensure unique file name for Final output
    output_path = f"{output_start}_{daystamp}.{EXTENSION}"
    counter = 1
    while os.path.exists(output_path):
        counter += 1
        output_path = f"{output_start}_{daystamp}_{counter}.{EXTENSION}"
    
    return output_path

# Send sequence to Adobe Media Encoder
def send_to_media_encoder(sequence, project, output_type, preset_path):
    print(f"Sending {output_type} sequence to Adobe Media Encoder...")

    # Ensure Media Encoder is launched
    pymiere.objects.app.encoder.launchEncoder()

    # Generate daystamp and output path
    today = datetime.date.today()
    daystamp = f"{today.day}{DUTCH_MONTHS[today.month]}"
    output_path = create_output_path(project.path, output_type, daystamp)

    # Ensure directory exists
    directory = os.path.dirname(output_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory {directory} created.")
    
    # Handle existing file (known Adobe Media Encoder bug: cannot overwrite)
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Existing file {output_path} deleted.")

    print(f"Destination: {output_path}")
    print(f"Using preset: {preset_path}")

    # Add job to Media Encoder queue
    pymiere.objects.app.encoder.encodeSequence(
        sequence,
        output_path,
        preset_path,
        pymiere.objects.app.encoder.ENCODE_IN_TO_OUT,  # Export In/Out range
        removeOnCompletion=False,  # Keep job in queue after completion
        startQueueImmediately=False
    )

# Run main function
main()
