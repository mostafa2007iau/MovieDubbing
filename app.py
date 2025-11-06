import os
import uuid
import threading
import time
import traceback
from datetime import datetime, timedelta
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
TASK_EXPIRATION_HOURS = 1
YDL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Global State ---
tasks = {}
tasks_lock = threading.Lock()
WHISPER_MODEL = whisper.load_model("base")

# --- Helper Functions (Refactored for Professional Error Handling) ---

def generate_filename(extension):
    return f"{uuid.uuid4()}.{extension}"

def cleanup_temp_files(*files):
    for file in files:
        if file and os.path.exists(file):
            try: os.remove(file)
            except OSError as e: print(f"Error deleting temporary file {file}: {e}")

def download_audio(video_url):
    """Downloads audio and raises an exception on any error."""
    try:
        audio_filename = generate_filename("mp3")
        audio_path = os.path.join(TEMP_DIR, audio_filename)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'outtmpl': os.path.join(TEMP_DIR, os.path.splitext(audio_filename)[0]),
            'noplaylist': True,
            'http_headers': {'User-Agent': YDL_USER_AGENT}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise RuntimeError("File not created or empty after download.")
        return audio_path
    except Exception as e:
        # Re-raise with a more informative message to be caught by the main handler
        raise RuntimeError(f"Failed in download_audio: {e}") from e

def transcribe_audio(audio_path):
    """Transcribes audio and raises an exception on any error."""
    try:
        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError("Audio file not found for transcription.")
        result = WHISPER_MODEL.transcribe(audio_path)
        return result.get('language'), result.get('text')
    except Exception as e:
        raise RuntimeError(f"Failed in transcribe_audio (Whisper): {e}") from e

def translate_text(text, source_lang, target_lang):
    """Translates text and raises an exception on any error."""
    try:
        if not text: return "" # Return empty if there's nothing to translate
        return ts.translate_text(text, from_language=source_lang, to_language=target_lang)
    except Exception as e:
        raise RuntimeError(f"Failed in translate_text: {e}") from e

def synthesize_speech(text, lang):
    """Synthesizes speech and raises an exception on any error."""
    try:
        audio_filename = generate_filename("mp3")
        audio_path = os.path.join(TEMP_DIR, audio_filename)
        tts = gTTS(text=text, lang=lang); tts.save(audio_path)
        return audio_path
    except Exception as e:
        raise RuntimeError(f"Failed in synthesize_speech (gTTS): {e}") from e

def combine_video_and_audio(video_url, dubbed_audio_path):
    """Combines video/audio and raises an exception on any error."""
    temp_video_path = None
    try:
        video_filename, temp_video_filename = generate_filename("mp4"), generate_filename("mp4")
        video_path = os.path.join(DOWNLOAD_DIR, video_filename)
        temp_video_path = os.path.join(TEMP_DIR, temp_video_filename)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]', 'outtmpl': temp_video_path, 'noplaylist': True,
            'http_headers': {'User-Agent': YDL_USER_AGENT}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        video_input = ffmpeg.input(temp_video_path); audio_input = ffmpeg.input(dubbed_audio_path)
        ffmpeg.output(video_input.video, audio_input.audio, video_path, vcodec='copy', acodec='aac').run(overwrite_output=True, quiet=True)
        return video_path
    except Exception as e:
        raise RuntimeError(f"Failed in combine_video_and_audio (ffmpeg): {e}") from e
    finally:
        cleanup_temp_files(temp_video_path)

def download_original_video(video_url):
    """Downloads original video and raises an exception on any error."""
    try:
        video_filename = generate_filename("mp4")
        video_path = os.path.join(DOWNLOAD_DIR, video_filename)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'outtmpl': video_path,
            'noplaylist': True, 'http_headers': {'User-Agent': YDL_USER_AGENT}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        return video_path
    except Exception as e:
        raise RuntimeError(f"Failed in download_original_video: {e}") from e

# --- Background Task Management ---
def cleanup_old_tasks():
    while True:
        time.sleep(60 * 60)
        with tasks_lock:
            expiration_time = datetime.now() - timedelta(hours=TASK_EXPIRATION_HOURS)
            tasks_to_delete = []
            for task_id, data in tasks.items():
                if data.get('timestamp', datetime.now()) < expiration_time:
                    tasks_to_delete.append(task_id)
                    if data.get('status') == 'success' and 'result' in data:
                        result = data['result']
                        files_to_delete = [os.path.basename(result.get('dubbed_video_url','')), os.path.basename(result.get('original_video_url',''))]
                        for filename in files_to_delete:
                            if not filename: continue
                            try:
                                file_path = os.path.join(DOWNLOAD_DIR, filename)
                                if os.path.exists(file_path): os.remove(file_path)
                            except OSError as e: print(f"Error deleting file {filename}: {e}")
            for task_id in tasks_to_delete: del tasks[task_id]

def process_task(task_id, video_url, target_lang):
    def update_status(status, message, result=None):
        with tasks_lock:
            task_data = {'status': status, 'message': message, 'timestamp': datetime.now()}
            if result: task_data['result'] = result
            tasks[task_id] = task_data

    original_audio_path = dubbed_audio_path = None
    try:
        update_status('processing', '۱/۶: در حال دانلود صدا...')
        original_audio_path = download_audio(video_url)

        update_status('processing', '۲/۶: در حال تشخیص گفتار...')
        source_lang, original_text = transcribe_audio(original_audio_path)

        update_status('processing', '۳/۶: در حال ترجمه متن...')
        translated_text = translate_text(original_text, source_lang, target_lang)

        update_status('processing', '۴/۶: در حال تولید صدای دوبله...')
        dubbed_audio_path = synthesize_speech(translated_text, target_lang)

        update_status('processing', '۵/۶: در حال ترکیب ویدیو و صدا...')
        dubbed_video_path = combine_video_and_audio(video_url, dubbed_audio_path)

        update_status('processing', '۶/۶: در حال آماده‌سازی نسخه اصلی...')
        original_video_path = download_original_video(video_url)

        final_result = {
            'dubbed_video_url': f'/downloads/{os.path.basename(dubbed_video_path)}',
            'original_text': original_text, 'translated_text': translated_text,
        }
        if original_video_path: final_result['original_video_url'] = f'/downloads/{os.path.basename(original_video_path)}'

        update_status('success', 'پردازش با موفقیت انجام شد!', final_result)

    except Exception as e:
        # Log the full technical error to the console for debugging
        print(f"--- Task {task_id} failed ---")
        traceback.print_exc()
        print("--------------------")
        # Send the specific, technical error message to the user
        update_status('error', f"خطا در پردازش: {e}")
    finally:
        cleanup_temp_files(original_audio_path, dubbed_audio_path)

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def start_processing():
    data = request.get_json()
    if not data or 'url' not in data or 'lang' not in data:
        return jsonify({'error': 'درخواست نامعتبر است.'}), 400

    task_id = str(uuid.uuid4())
    with tasks_lock:
        tasks[task_id] = {'status': 'queued', 'message': 'وظیفه در صف قرار گرفت.', 'timestamp': datetime.now()}

    thread = threading.Thread(target=process_task, args=(task_id, data['url'], data['lang']))
    thread.start()

    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def task_status(task_id):
    with tasks_lock:
        task = tasks.get(task_id, {}).copy()

    if not task:
        return jsonify({'status': 'error', 'message': 'وظیفه یافت نشد.'}), 404
    return jsonify(task)

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
    cleanup_thread.start()
    app.run(debug=False, host='0.0.0.0', port=5000)
