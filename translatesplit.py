import click
import subprocess
import os

@click.command()
@click.option('-n', '--name', default='output_video', help='Output video file path (without extension)')
@click.option('-l', '--lang', help='Input language')
@click.argument('url', type=click.STRING)

def translate_videos(url, name, lang):
    
    mp4_path = f"files/{name}.mp4"
    webm_path = f"files/{name}.webm"
    mkv_path = f"files/{name}.mkv"
    counter = 2
    name_changed = False

    #If the filename already exists, add a number at the end to avoid overriding
    while os.path.exists(mp4_path) or os.path.exists(webm_path) or os.path.exists(mkv_path):
        new_name = name+str(counter)
        mp4_path = f"files/{new_name}.mp4"
        webm_path = f"files/{new_name}.webm"
        mkv_path = f"files/{new_name}.mkv"
        counter += 1
        name_changed = True

    if name_changed:
        click.echo(f"{name} already exists, changed name to {new_name}")
        name = new_name

    
    # Download video with yt-dlp
    command1 = f"yt-dlp -o files/{name}.%(ext)s {url}"
    subprocess.run(command1, shell=True)
    
    #Create an audio file from the video
    #If yt-dlp downloads the video as an mp4
    if os.path.exists(mp4_path):
        command2 = f"ffmpeg -i files/{name}.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 2 files/{name}.wav"
    #If yt-dlp downloads the video as a webm
    elif os.path.exists(webm_path):
        command2 = f"ffmpeg -i files/{name}.webm -vn -acodec pcm_s16le -ar 16000 -ac 2 files/{name}.wav"
    #If yt-dlp downloads the video as an mkv
    elif os.path.exists(mkv_path):
        command2 = f"ffmpeg -i files/{name}.mkv -vn -acodec pcm_s16le -ar 16000 -ac 2 files/{name}.wav"
    
    #Will add support for other formats if I encounter them
    else:
        click.echo("Unsupported video format")
        return

    subprocess.run(command2, shell=True)
    
    command3 = f"ffmpeg -i files/{name}.wav -f segment -segment_time 300 -c copy files/{name}_%d.wav"
    subprocess.run(command3, shell=True)

    #Translate the audio file and create english subtitles
    segment_subtitles = []
    segment_audiofiles = []
    if not all([lang]):
        #If no input language is specified, detect the language automatically
        counter = 0 
        while os.path.exists(f"files/{name}_{counter}.wav"):
            
            command4 = f"main -ovtt -tr -l auto -m models/ggml-large.bin -pp -of files/{name}_{counter} files/{name}_{counter}.wav"
            segment_subtitles.append(f"files/{name}_{counter}.vtt")
            segment_audiofiles.append(f"files/{name}_{counter}.wav")
            subprocess.run(command4, shell=True)
            
            counter += 1

    else:
        lang = lang.lower()

        counter = 0 
        while os.path.exists(f"files/{name}_{counter}.wav"):
            
            command4 = f"main -ovtt -tr -l {lang} -m models/ggml-large.bin -pp -of files/{name}_{counter} files/{name}_{counter}.wav"
            segment_subtitles.append(f"files/{name}_{counter}.vtt")
            segment_audiofiles.append(f"files/{name}_{counter}.wav")
            subprocess.run(command4, shell=True)
            
            counter += 1

    
    
    combine_subtitle_files_webvtt(segment_subtitles, f"files/{name}.vtt")

    
 
    #Embed the subtitles in the downloaded video
    if os.path.exists(mp4_path):
        command5 = f"ffmpeg -i files/{name}.mp4 -i files/{name}.vtt -c:v copy -c:a copy -c:s mov_text files/{name}_subbed.mp4"
    elif os.path.exists(webm_path):    
        command5 = f"ffmpeg -i files/{name}.webm -i files/{name}.vtt -c:v copy -c:a copy -c:s copy files/{name}_subbed.webm"
    elif os.path.exists(mkv_path): 
        command5 = f"ffmpeg -i files/{name}.mkv -i files/{name}.vtt -c:v copy -c:a copy -c:s copy files/{name}_subbed.mkv"
    subprocess.run(command5, shell=True)

    for segment in segment_audiofiles:
        os.remove(segment)
    


    if os.path.exists(mp4_path):
        click.echo(f"Created {name}_subbed.mp4")
    elif os.path.exists(webm_path):
        click.echo(f"Created {name}_subbed.webm")
    elif os.path.exists(mkv_path): 
        click.echo(f"Created {name}_subbed.mkv")

    return
    
def adjust_timestamps_webvtt(subtitle_file, offset_seconds):
    with open(subtitle_file, 'r') as file:
        lines = file.readlines()

        lines = lines[1:]

    for i in range(len(lines)):
        if ' --> ' in lines[i]:
            start, end = lines[i].strip().split(' --> ')

            start_time, start_millis = start.split('.')
            end_time, end_millis = end.split('.')

            start_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], start_time.split(':')))
            end_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], end_time.split(':')))

            start_seconds += offset_seconds
            end_seconds += offset_seconds

            lines[i] = f"{start_seconds // 3600:02d}:{(start_seconds % 3600) // 60:02d}:{start_seconds % 60:02d}.{start_millis} --> "
            lines[i] += f"{end_seconds // 3600:02d}:{(end_seconds % 3600) // 60:02d}:{end_seconds % 60:02d}.{end_millis}\n"

    return lines

def combine_subtitle_files_webvtt(segment_files, output_file):
    offset_seconds = 0
    with open(output_file, 'w') as output:
        output.writelines("WEBVTT")
        for segment in segment_files:
            lines = adjust_timestamps_webvtt(segment, offset_seconds)
            offset_seconds += 300  # Adjust the offset based on your segment length
            output.writelines(lines)
            output.writelines("\n")
    
    for segment in segment_files:
        os.remove(segment)

    return

translate_videos()