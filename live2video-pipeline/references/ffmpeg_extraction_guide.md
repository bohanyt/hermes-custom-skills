# ffmpeg Clip Extraction — Pitfalls & Strategies

## AV1 Source: Hardware Decode Required
**CRITICAL:** If source video is AV1 codec (check with `ffprobe -show_entries stream=codec_name`), software decode is extremely slow and will cause timeouts. **Must use CUDA hardware decode:**

```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -ss HH:MM:SS -i source.mkv -t DURATION_SEC -c:v h264_nvenc -preset p1 -rc cbr -b:v 8M -c:a aac -b:a 128k output.mp4
```

Without `-hwaccel cuda`, AV1 decode on CPU can take 10+ minutes per clip on RTX 3050 laptop. With hardware decode: ~15-40s per clip.

**How to detect AV1:** `ffprobe -v error -show_entries stream=codec_name -of csv=p=0 source.mp4` → shows `av1` instead of `h264`.

**Note:** Remuxing MP4→MKV (`-c:v copy -c:a copy`) does NOT help with AV1 decode speed — the codec is the same. Hardware decode is the only fix. MKV remux is fast (~130x speed, stream copy) but only helps with container-level seek, not decode.

## Use `-t` (Duration) Instead of `-to` (End Time)
**CRITICAL:** Using `-t DURATION` is more reliable than `-to END_TIME` for accurate clip extraction. `-to` can produce clips with incorrect durations due to keyframe alignment issues, while `-t` specifies exact duration from the seek point.

```bash
# GOOD — exact duration
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -ss 00:02:40 -i source.mkv -t 50 -c:v h264_nvenc -preset p1 -rc cbr -b:v 8M -c:a aac -b:a 128k output.mp4

# BAD — can produce wrong duration
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -ss 00:02:40 -i source.mkv -to 00:03:30 -c:v h264_nvenc -preset p1 -rc cbr -b:v 8M -c:a aac -b:a 128k output.mp4
```

## Stream Copy Duration Inaccuracy
`-c:v copy` snaps to nearest keyframe, not exact timestamp. A 60s clip can become 20+ min on large sources. **Always re-encode** for accurate boundaries: `-c:v h264_nvenc -preset p1 -rc cbr -b:v 8M`.

## Disk Space & Seek Performance
When disk >95% full, ffmpeg seek on large files (5GB+) becomes extremely slow (10+ min/clip). Keep 10-15% free. Clean old `testing/` outputs before extracting.

## NVENC on RTX 3050 Laptop
~3 fps for 1080p re-encode of full video. OK for individual clips (~15-40s each with `-preset p1`), too slow for full 2h pre-processing. Use `-preset p1` (fastest) for extraction, `-preset p3` for final concat.

## Windows File Locking
When ffmpeg crashes or is killed, output files can remain locked by the process, causing `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`.

**Fix:** Before retrying extraction, kill all ffmpeg processes:
```bash
taskkill /F /IM ffmpeg.exe
```
If files are still locked, rename them and extract with new filenames.

## Recommended Commands

### Extract from AV1 source (hardware decode, accurate duration):
```bash
ffmpeg -y -hwaccel cuda -hwaccel_output_format cuda -ss HH:MM:SS -i source.mkv -t DURATION_SEC -c:v h264_nvenc -preset p1 -rc cbr -b:v 8M -c:a aac -b:a 128k output.mp4
```

### Extract from H.264 source (no hardware decode needed):
```bash
ffmpeg -y -ss HH:MM:SS -i source.mp4 -t DURATION_SEC -c:v h264_nvenc -preset p1 -rc cbr -b:v 8M -c:a aac -b:a 128k output.mp4
```

### Concatenate many clips:
Create `concat.txt`:
```
file 'clip1.mp4'
file 'clip2.mp4'
...
```

Then:
```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -c:v h264_nvenc -preset p3 -rc vbr -b:v 10M -maxrate 12M -bufsize 20M -c:a aac -b:a 192k -movflags +faststart final.mp4
```

**Note:** Concatenating 41 clips takes ~5-10 minutes. The output file grows gradually — don't assume it's stuck if size is increasing.

### Remux to MKV (fast, no re-encode):
```bash
ffmpeg -y -i source.mp4 -c:v copy -c:a copy source.mkv
```
This is very fast (~130x speed) but does NOT improve AV1 decode performance. Only useful if container format is causing issues.
