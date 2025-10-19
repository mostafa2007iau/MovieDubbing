document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('process-form');
    const resultDiv = document.getElementById('result');
    const submitButton = form.querySelector('button');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const videoUrl = document.getElementById('video-url').value;
        const targetLang = document.getElementById('target-lang').value;

        // Disable button and show loading message
        submitButton.disabled = true;
        submitButton.textContent = 'در حال پردازش...';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<p>این فرآیند ممکن است چند دقیقه طول بکشد. لطفاً صبور باشید...</p>';

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: videoUrl,
                    lang: targetLang,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'خطایی در سرور رخ داد.');
            }

            displayResults(data);

        } catch (error) {
            resultDiv.innerHTML = `<p class="error">خطا: ${error.message}</p>`;
        } finally {
            // Re-enable button
            submitButton.disabled = false;
            submitButton.textContent = 'شروع پردازش';
        }
    });

    function displayResults(data) {
        let originalVideoLink = '';
        if (data.original_video_url) {
            originalVideoLink = `<a href="${data.original_video_url}" download class="download-link">دانلود ویدیوی اصلی</a>`;
        }

        resultDiv.innerHTML = `
            <h3>${data.message}</h3>

            <div class="video-player">
                <video controls width="100%">
                    <source src="${data.dubbed_video_url}" type="video/mp4">
                    مرورگر شما از تگ ویدیو پشتیبانی نمی‌کند.
                </video>
            </div>

            <div class="download-links">
                <a href="${data.dubbed_video_url}" download class="download-link">دانلود ویدیوی دوبله شده</a>
                ${originalVideoLink}
            </div>

            <div class="transcripts">
                <h4>متن اصلی (زبان شناسایی شده):</h4>
                <p class="transcript-box">${data.original_text}</p>

                <h4>متن ترجمه شده:</h4>
                <p class="transcript-box">${data.translated_text}</p>
            </div>
        `;
    }
});
