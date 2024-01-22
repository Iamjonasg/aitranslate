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
    
    #Translate the audio file and create english subtitles
    if not all([lang]):
        #If no input language is specified, detect the language automatically
        command3 = f"main -ovtt -tr -l auto -m models/ggml-large.bin -pp -of files/{name} files/{name}.wav"
    else:
        lang = lang.lower()
        command3 = f"main -ovtt -tr -l {lang} -m models/ggml-large.bin -pp -of files/{name} files/{name}.wav"

    #Embed the subtitles in the downloaded video
    if os.path.exists(mp4_path):
        command4 = f"ffmpeg -i files/{name}.mp4 -i files/{name}.vtt -c:v copy -c:a copy -c:s mov_text files/{name}_subbed.mp4"
    elif os.path.exists(webm_path):    
        command4 = f"ffmpeg -i files/{name}.webm -i files/{name}.vtt -c:v copy -c:a copy -c:s copy files/{name}_subbed.webm"
    elif os.path.exists(mkv_path): 
        command4 = f"ffmpeg -i files/{name}.mkv -i files/{name}.vtt -c:v copy -c:a copy -c:s copy files/{name}_subbed.mkv"
    
    subprocess.run(command2, shell=True)
    subprocess.run(command3, shell=True)
    subprocess.run(command4, shell=True)
    if os.path.exists(mp4_path):
        click.echo(f"Created {name}_subbed.mp4")
    elif os.path.exists(webm_path):
        click.echo(f"Created {name}_subbed.webm")

    return

translate_videos()