import argparse
import json
import subprocess
import os

def get_alphabet_label(index):
    """Converts an integer index to an alphabet label (0=a, 1=b, ..., 25=z, 26=aa, etc.)."""
    label = ""
    while index >= 0:
        label = chr(97 + (index % 26)) + label
        index = (index // 26) - 1
    return label

def format_timestamp_for_filename(timestamp):
    """Converts HH:MM:SS to HHhMMmSSs for Windows filename compatibility."""
    if not timestamp:
        return "unknown"
    # Replace first : with h, second : with m, and add s at the end
    formatted = timestamp.replace(':', 'h', 1).replace(':', 'm', 1) + 's'
    return formatted

def cut_video(input_file, start_time, end_time, output_file):
    """Cuts a video segment using ffmpeg with stream copying for speed."""
    command = [
        'ffmpeg',
        '-ss', start_time,
        '-to', end_time,
        '-i', input_file,
        '-c', 'copy',
        '-avoid_negative_ts', 'make_zero',
        '-y',
        output_file
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error cutting segment {start_time} to {end_time}: {e.stderr.decode()}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Cut video segments based on a JSON timestamp file and save them as separate clips.")
    parser.add_argument("--input", required=True, help="Path to the raw input video file (e.g., livestream.mp4)")
    parser.add_argument("--json", required=True, help="Path to the JSON file containing start and end timestamps")
    
    args = parser.parse_args()

    # Load timestamps
    try:
        with open(args.json, 'r') as f:
            timestamps = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    if not isinstance(timestamps, list):
        print("JSON file should contain a list of timestamp objects: [{'start': '...', 'end': '...'}, ...]")
        return

    # Create output directory
    output_dir = "final_cuts"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print(f"Processing {len(timestamps)} segments...")
    
    success_count = 0
    for i, ts in enumerate(timestamps):
        start = ts.get('start')
        end = ts.get('end')
        
        if not start or not end:
            print(f"Skipping segment {i+1} due to missing start or end timestamp.")
            continue
            
        # Generate filename components
        label = get_alphabet_label(i)
        start_fmt = format_timestamp_for_filename(start)
        end_fmt = format_timestamp_for_filename(end)
        
        filename = f"{label}_{start_fmt}_{end_fmt}.mp4"
        output_path = os.path.join(output_dir, filename)
        
        print(f"Cutting segment {i+1}/{len(timestamps)}: {start} -> {end} as {filename}")
        
        if cut_video(args.input, start, end, output_path):
            success_count += 1
        else:
            print(f"Failed to cut segment {i+1}")

    print(f"\nProcessing complete. {success_count}/{len(timestamps)} clips saved in '{output_dir}/'.")

if __name__ == "__main__":
    main()