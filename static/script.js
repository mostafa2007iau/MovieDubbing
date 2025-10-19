document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('process-form');
    const resultDiv = document.getElementById('result');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const videoUrl = document.getElementById('video-url').value;
        const targetLang = document.getElementById('target-lang').value;

        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<p>در حال پردازش... لطفاً منتظر بمانید.</p>';

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

            if (!response.ok) {
                throw new Error('خطایی در ارتباط با سرور رخ داد.');
            }

            const data = await response.json();

            // در مراحل بعدی، نتایج واقعی در اینجا نمایش داده خواهند شد
            resultDiv.innerHTML = `
                <h3>پاسخ اولیه دریافت شد:</h3>
                <p>آدرس ویدیو: ${data.url}</p>
                <p>زبان مقصد: ${data.lang}</p>
            `;

        } catch (error) {
            resultDiv.innerHTML = `<p style="color: red;">خطا: ${error.message}</p>`;
        }
    });
});
