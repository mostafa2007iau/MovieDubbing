document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('process-form');
    const resultDiv = document.getElementById('result');
    const submitButton = form.querySelector('button');
    let pollingInterval;

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (pollingInterval) clearInterval(pollingInterval);

        const videoUrl = document.getElementById('video-url').value;
        const targetLang = document.getElementById('target-lang').value;

        submitButton.disabled = true;
        submitButton.textContent = 'در حال ارسال...';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<p>درخواست شما ثبت شد. در حال شروع پردازش...</p>';

        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: videoUrl, lang: targetLang }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'خطا در ارسال درخواست.');
            }

            pollStatus(data.task_id);

        } catch (error) {
            resultDiv.innerHTML = `<p class="error">خطا: ${error.message}</p>`;
            submitButton.disabled = false;
            submitButton.textContent = 'شروع پردازش';
        }
    });

    function pollStatus(taskId) {
        submitButton.textContent = 'در حال پردازش...';
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${taskId}`);
                const data = await response.json();

                if (data.status === 'processing') {
                    resultDiv.innerHTML = `<p>${data.message}</p>`;
                } else if (data.status === 'success') {
                    clearInterval(pollingInterval);
                    resultDiv.innerHTML = '<h3>پردازش با موفقیت انجام شد!</h3>';
                    displayResults(data.result);
                    submitButton.disabled = false;
                    submitButton.textContent = 'شروع پردازش';
                } else if (data.status === 'error') {
                    clearInterval(pollingInterval);
                    resultDiv.innerHTML = `<p class="error">خطا در پردازش: ${data.message}</p>`;
                    submitButton.disabled = false;
                    submitButton.textContent = 'شروع پردازش';
                }
            } catch (error) {
                clearInterval(pollingInterval);
                resultDiv.innerHTML = `<p class="error">خطا در بررسی وضعیت: ${error.message}</p>`;
                submitButton.disabled = false;
                submitButton.textContent = 'شروع پردازش';
            }
        }, 3000); // Check status every 3 seconds
    }

    function displayResults(data) {
        let originalVideoLink = '';
        if (data.original_video_url) {
            originalVideoLink = `<a href="${data.original_video_url}" download class="download-link">دانلود ویدیوی اصلی</a>`;
        }

        const resultHTML = `
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
        // Replace the content with the final results
        resultDiv.innerHTML = resultHTML;
    }
});
