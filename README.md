# Video Dubbing and Translation Tool

This project is a web-based tool that automates the process of video dubbing and translation. It can take a video URL from popular platforms like YouTube, automatically detect the spoken language, translate it into a desired language, and generate a new video file with the dubbed audio.

---

<div dir="rtl" align="right">

# ابزار دوبله و ترجمه ویدیو

این پروژه یک ابزار تحت وب است که فرآیند دوبله و ترجمه ویدیو را به صورت خودکار انجام می‌دهد. این ابزار می‌تواند URL ویدیو را از پلتفرم‌های معروفی مانند یوتیوب دریافت کرده، زبان گفتار را به صورت خودکار تشخیص دهد، آن را به زبان دلخواه ترجمه کند و یک فایل ویدیوی جدید با صدای دوبله شده تولید نماید.

</div>

---

## Features

-   **Automatic Language Detection**: Uses OpenAI's Whisper model to accurately detect the source language of the video.
-   **Text Translation**: Translates the transcribed text into multiple target languages.
-   **AI-Powered Dubbing**: Generates a new audio track in the target language using Text-to-Speech (TTS) technology.
-   **Video Processing**: Merges the original video stream with the newly generated dubbed audio.
-   **Download Options**: Provides download links for both the final dubbed video and the original video.
-   **Web-Based Interface**: A simple and user-friendly interface built with Flask.

<div dir="rtl" align="right">

## قابلیت‌ها

-   **تشخیص خودکار زبان**: با استفاده از مدل Whisper شرکت OpenAI، زبان اصلی ویدیو را با دقت بالا تشخیص می‌دهد.
-   **ترجمه متن**: متن استخراج شده از ویدیو را به زبان‌های مختلف ترجمه می‌کند.
-   **دوبله با هوش مصنوعی**: یک فایل صوتی جدید به زبان مقصد با استفاده از تکنولوژی تبدیل متن به گفتار (TTS) تولید می‌کند.
-   **پردازش ویدیو**: ویدیوی اصلی را با صدای دوبله شده جدید ادغام می‌کند.
-   **امکان دانلود**: لینک دانلود برای ویدیوی نهایی دوبله شده و همچنین ویدیوی اصلی را فراهم می‌کند.
-   **رابط کاربری تحت وب**: یک رابط کاربری ساده و کاربرپسند که با استفاده از فلسک (Flask) ساخته شده است.

</div>

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **Python 3.9+**
-   **pip** (Python package installer)
-   **FFmpeg**: This is a critical dependency for audio and video processing.

### Installing FFmpeg

**On Debian/Ubuntu:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**On macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**On Windows (using Chocolatey):**
```bash
choco install ffmpeg
```

For other systems, please refer to the [official FFmpeg download page](https://ffmpeg.org/download.html).

<div dir="rtl" align="right">

## پیش‌نیازها

قبل از شروع، اطمینان حاصل کنید که موارد زیر روی سیستم شما نصب شده باشند:

-   **پایتون 3.9 به بالا**
-   **pip** (مدیر بسته پایتون)
-   **FFmpeg**: این یک وابستگی حیاتی برای پردازش صدا و تصویر است.

### نصب FFmpeg

**روی سیستم‌عامل دبیان/اوبونتو:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**روی سیستم‌عامل macOS (با استفاده از Homebrew):**
```bash
brew install ffmpeg
```

**روی سیستم‌عامل ویندوز (با استفاده از Chocolatey):**
```bash
choco install ffmpeg
```

برای سایر سیستم‌عامل‌ها، لطفاً به [صفحه رسمی دانلود FFmpeg](https://ffmpeg.org/download.html) مراجعه کنید.

</div>

---

## Installation and Setup

Follow these steps to get the project running on your local machine.

**1. Clone the repository:**
```bash
git clone <repository-url>
cd <repository-directory>
```

**2. Create and activate a virtual environment:**

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\\venv\\Scripts\\activate
```

**3. Install the required packages:**

All dependencies are listed in the `requirements.txt` file.
```bash
pip install -r requirements.txt
```
*Note: The installation of `torch` and `openai-whisper` might take a significant amount of time and disk space.*

<div dir="rtl" align="right">

## نصب و راه‌اندازی

برای اجرای پروژه روی سیستم محلی خود، مراحل زیر را دنبال کنید.

**۱. کلون کردن مخزن:**
```bash
git clone <repository-url>
cd <repository-directory>
```

**۲. ایجاد و فعال‌سازی محیط مجازی:**

اکیداً توصیه می‌شود که برای مدیریت وابستگی‌های پروژه از یک محیط مجازی استفاده کنید.

```bash
# ایجاد محیط مجازی
python3 -m venv venv

# فعال‌سازی آن
# روی لینوکس/macOS:
source venv/bin/activate
# روی ویندوز:
.\\venv\\Scripts\\activate
```

**۳. نصب بسته‌های مورد نیاز:**

تمام وابستگی‌ها در فایل `requirements.txt` لیست شده‌اند.
```bash
pip install -r requirements.txt
```
*توجه: نصب بسته‌های `torch` و `openai-whisper` ممکن است به زمان و فضای دیسک قابل توجهی نیاز داشته باشد.*

</div>

---

## How to Run the Application

Once the installation is complete, you can start the Flask web server with the following command:

```bash
python app.py
```

The application will be running at: **http://127.0.0.1:5000**

Open this URL in your web browser. You can now enter a video URL, select a target language, and start the dubbing process.

<div dir="rtl" align="right">

## نحوه اجرای برنامه

پس از اتمام نصب، می‌توانید سرور وب فلسک را با دستور زیر راه‌اندازی کنید:

```bash
python app.py
```

برنامه روی آدرس زیر در حال اجرا خواهد بود: **http://127.0.0.1:5000**

این آدرس را در مرورگر وب خود باز کنید. اکنون می‌توانید URL ویدیو را وارد کرده، زبان مقصد را انتخاب کنید و فرآیند دوبله را آغاز نمایید.

</div>
