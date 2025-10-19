import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import whisper
import translators as ts
from gtts import gTTS
import ffmpeg

app = Flask(__name__)

# --- Configurations ---
TEMP_DIR = "temp"
DOWNLOAD_DIR = "downloads"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Helper Functions ---

def generate_filename(extension):
    """Generates a unique filename with the given extension."""
    return f"{uuid.uuid4()}.{extension}"

def download_audio(video_url):
    """
    Downloads the audio from a video URL and saves it as an MP3 file.
    Returns the path to the downloaded audio file.
    """
    try:
        audio_filename = generate_filename("mp3")
        audio_path = os.path.join(TEMP_DIR, audio_filename)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(TEMP_DIR, os.path.splitext(audio_filename)[0])
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        return audio_path
    except Exception as e:
        print(f"Error in download_audio: {e}")
        return None

def transcribe_audio(audio_path):
    """
    Transcribes the given audio file using Whisper.
    Returns the detected language and the transcribed text.
    """
    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result['language'], result['text']
    except Exception as e:
        print(f"Error in transcribe_audio: {e}")
        return None, None

def translate_text(text, source_lang, target_lang):
    """
    Translates text from a source language to a target language.
    Returns the translated text.
    """
    try:
        translated_text = ts.translate_text(text, from_language=source_lang, to_language=target_lang)
        return translated_text
    except Exception as e:
        print(f"Error in translate_text: {e}")
        return None

def synthesize_speech(text, lang):
    """
    Synthesizes speech from text and saves it as an MP3 file.
    Returns the path to the synthesized audio file.
    """
    try:
        audio_filename = generate_filename("mp3")
        audio_path = os.path.join(TEMP_DIR, audio_filename)

        tts = gTTS(text=text, lang=lang)
        tts.save(audio_path)

        return audio_path
    except Exception as e:
        print(f"Error in synthesize_speech: {e}")
        return None

def combine_video_and_audio(video_url, dubbed_audio_path):
    """
    Downloads the video from the URL, removes its original audio,
    and merges it with the new dubbed audio.
    Returns the path to the final dubbed video.
    """
    try:
        video_filename = generate_filename("mp4")
        video_path = os.path.join(DOWNLOAD_DIR, video_filename)

        temp_video_filename = generate_filename("mp4")
        temp_video_path = os.path.join(TEMP_DIR, temp_video_filename)

        # Download the video file (without audio)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]',
            'outtmpl': temp_video_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Combine the video and the new audio using ffmpeg
        video_input = ffmpeg.input(temp_video_path)
        audio_input = ffmpeg.input(dubbed_audio_path)

        ffmpeg.output(video_input.video, audio_input.audio, video_path, vcodec='copy', acodec='aac').run(overwrite_output=True)

        return video_path
    except Exception as e:
        print(f"Error in combine_video_and_audio: {e}")
        return None
    finally:
        # Clean up the temporary video file
        if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
            os.remove(temp_video_path)

def download_original_video(video_url):
    """
    Downloads the original video with the best quality.
    Returns the path to the downloaded video.
    """
    try:
        video_filename = generate_filename("mp4")
        video_path = os.path.join(DOWNLOAD_DIR, video_filename)

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': video_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        return video_path
    except Exception as e:
        print(f"Error in download_original_video: {e}")
        return None

# --- Main Application ---

@app.route('/')
def index():
    return render_template('index.html')

def cleanup_temp_files(*files):
    """Deletes the given files from the temp directory."""
    for file in files:
        if file and os.path.exists(file):
            try:
                os.remove(file)
            except OSError as e:
                print(f"Error deleting file {file}: {e}")

@app.route('/process', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('url')
    target_lang = data.get('lang')

    if not video_url or not target_lang:
        return jsonify({'error': 'URL و زبان مقصد الزامی است.'}), 400

    # --- Step 1: Download Audio ---
    original_audio_path = download_audio(video_url)
    if not original_audio_path:
        return jsonify({'error': 'دانلود صدا با مشکل مواجه شد.'}), 500

    # --- Step 2: Transcribe Audio ---
    source_lang, original_text = transcribe_audio(original_audio_path)
    if not original_text:
        cleanup_temp_files(original_audio_path)
        return jsonify({'error': 'تشخیص گفتار با مشکل مواجه شد.'}), 500

    # --- Step 3: Translate Text ---
    translated_text = translate_text(original_text, source_lang, target_lang)
    if not translated_text:
        cleanup_temp_files(original_audio_path)
        return jsonify({'error': 'ترجمه متن با مشکل مواجه شد.'}), 500

    # --- Step 4: Synthesize Speech (Dubbed Audio) ---
    dubbed_audio_path = synthesize_speech(translated_text, target_lang)
    if not dubbed_audio_path:
        cleanup_temp_files(original_audio_path)
        return jsonify({'error': 'تولید صدای دوبله با مشکل مواجه شد.'}), 500

    # --- Step 5: Combine Video with Dubbed Audio ---
    dubbed_video_path = combine_video_and_audio(video_url, dubbed_audio_path)
    if not dubbed_video_path:
        cleanup_temp_files(original_audio_path, dubbed_audio_path)
        return jsonify({'error': 'ترکیب ویدیو و صدای دوبله با مشکل مواجه شد.'}), 500

    # --- Step 6: Download Original Video (Optional) ---
    original_video_path = download_original_video(video_url)

    # --- Step 7: Cleanup ---
    # The temp_video_path is not directly available here, so we need to find it.
    # A better approach would be to return it from combine_video_and_audio.
    # For now, let's assume the combine function cleans up its own temp video.
    # Let's modify combine_video_and_audio to handle its own cleanup.
    cleanup_temp_files(original_audio_path, dubbed_audio_path)

    # --- Step 8: Return Results ---
    response = {
        'message': 'پردازش با موفقیت انجام شد!',
        'dubbed_video_url': f'/downloads/{os.path.basename(dubbed_video_path)}',
        'original_text': original_text,
        'translated_text': translated_text,
    }
    if original_video_path:
        response['original_video_url'] = f'/downloads/{os.path.basename(original_video_path)}'

    return jsonify(response)


@app.route('/downloads/<filename>')
def download_file(filename):
    """Serves files from the download directory."""
    return send_from_directory(DOWNLOAD_DIR, filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
