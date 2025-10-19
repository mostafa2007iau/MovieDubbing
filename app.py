from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    data = request.get_json()
    video_url = data.get('url')
    target_lang = data.get('lang')

    # در این مرحله، فقط داده‌های دریافتی را برمی‌گردانیم
    # منطق اصلی پردازش در مراحل بعدی اضافه خواهد شد
    return jsonify({
        'message': 'اطلاعات با موفقیت دریافت شد.',
        'url': video_url,
        'lang': target_lang
    })

if __name__ == '__main__':
    app.run(debug=True)
