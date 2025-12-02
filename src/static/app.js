const API_BASE = window.location.origin;

let currentSummaryFile = null;

// DOM Elements
const folderIdInput = document.getElementById('folderId');
const subjectNameInput = document.getElementById('subjectName');
const semesterInput = document.getElementById('semester');
const btnSummarize = document.getElementById('btnSummarize');
const summarizeStatus = document.getElementById('summarizeStatus');
const toolsSection = document.getElementById('tools-section');

// Tabs
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Tools
const summaryContent = document.getElementById('summaryContent');
const downloadLink = document.getElementById('downloadLink');

const btnGenerateQuiz = document.getElementById('btnGenerateQuiz');
const quizContainer = document.getElementById('quizContainer');

const btnGenerateFlashcards = document.getElementById('btnGenerateFlashcards');
const flashcardsContainer = document.getElementById('flashcardsContainer');

const chatHistory = document.getElementById('chatHistory');
const chatInput = document.getElementById('chatInput');
const btnSendChat = document.getElementById('btnSendChat');


// Event Listeners
btnSummarize.addEventListener('click', handleSummarize);

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        // Add active class
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
});

btnGenerateQuiz.addEventListener('click', generateQuiz);
btnGenerateFlashcards.addEventListener('click', generateFlashcards);
btnSendChat.addEventListener('click', sendChatMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatMessage();
});


async function handleSummarize() {
    const folderId = folderIdInput.value.trim();
    const subjectName = subjectNameInput.value.trim();
    const semester = semesterInput.value.trim();

    if (!folderId || !subjectName) {
        alert('Please enter Folder ID and Subject Name');
        return;
    }

    summarizeStatus.textContent = 'Summarizing... This may take a minute.';
    btnSummarize.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/summarize-folder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folderId, subjectName, semester })
        });

        const data = await response.json();

        if (response.ok) {
            summarizeStatus.textContent = 'Success! Summary generated.';
            currentSummaryFile = data.summary_file;
            showTools(data);
        } else {
            summarizeStatus.textContent = `Error: ${data.detail || 'Unknown error'}`;
        }
    } catch (err) {
        summarizeStatus.textContent = `Error: ${err.message}`;
    } finally {
        btnSummarize.disabled = false;
    }
}

async function showTools(data) {
    toolsSection.classList.remove('hidden');
    downloadLink.href = data.summary_url;

    // Load summary content
    try {
        const resp = await fetch(data.summary_url);
        const text = await resp.text();
        summaryContent.innerHTML = marked.parse(text);
    } catch (e) {
        summaryContent.innerHTML = 'Failed to load summary text.';
    }
}

async function generateQuiz() {
    if (!currentSummaryFile) return;

    quizContainer.innerHTML = '<p>Generating quiz...</p>';
    btnGenerateQuiz.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/generate-quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ summary_file: currentSummaryFile })
        });
        const data = await response.json();
        renderQuiz(data.quiz);
    } catch (e) {
        quizContainer.innerHTML = `<p>Error: ${e.message}</p>`;
    } finally {
        btnGenerateQuiz.disabled = false;
    }
}

function renderQuiz(quizData) {
    quizContainer.innerHTML = '';
    if (!quizData || quizData.length === 0) {
        quizContainer.innerHTML = '<p>No quiz generated.</p>';
        return;
    }

    quizData.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'quiz-item';

        let optionsHtml = '';
        item.options.forEach(opt => {
            optionsHtml += `<li class="quiz-option" onclick="checkAnswer(this, '${opt.replace(/'/g, "\\'")}', '${item.answer.replace(/'/g, "\\'")}')">${opt}</li>`;
        });

        div.innerHTML = `
            <div class="quiz-question">${index + 1}. ${item.question}</div>
            <ul class="quiz-options">${optionsHtml}</ul>
            <div class="quiz-explanation">${item.explanation}</div>
        `;
        quizContainer.appendChild(div);
    });
}

window.checkAnswer = function(el, selected, correct) {
    const parent = el.parentElement;
    // Disable clicks
    Array.from(parent.children).forEach(c => c.style.pointerEvents = 'none');

    if (selected === correct) {
        el.classList.add('correct');
    } else {
        el.classList.add('wrong');
        // Highlight correct one
        Array.from(parent.children).forEach(c => {
            if (c.textContent.trim() === correct.trim()) c.classList.add('correct');
        });
    }
    // Show explanation
    parent.nextElementSibling.style.display = 'block';
}

async function generateFlashcards() {
    if (!currentSummaryFile) return;

    flashcardsContainer.innerHTML = '<p>Generating flashcards...</p>';
    btnGenerateFlashcards.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/generate-flashcards`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ summary_file: currentSummaryFile })
        });
        const data = await response.json();
        renderFlashcards(data.flashcards);
    } catch (e) {
        flashcardsContainer.innerHTML = `<p>Error: ${e.message}</p>`;
    } finally {
        btnGenerateFlashcards.disabled = false;
    }
}

function renderFlashcards(cards) {
    flashcardsContainer.innerHTML = '';
    if (!cards || cards.length === 0) {
        flashcardsContainer.innerHTML = '<p>No flashcards generated.</p>';
        return;
    }

    cards.forEach(card => {
        const div = document.createElement('div');
        div.className = 'flashcard';
        div.onclick = () => div.classList.toggle('flipped');
        div.innerHTML = `
            <div class="flashcard-inner">
                <div class="flashcard-front">${card.front}</div>
                <div class="flashcard-back">${card.back}</div>
            </div>
        `;
        flashcardsContainer.appendChild(div);
    });
}

async function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text || !currentSummaryFile) return;

    // Append user message
    appendMessage(text, 'user');
    chatInput.value = '';

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                summary_file: currentSummaryFile,
                question: text
            })
        });
        const data = await response.json();
        appendMessage(data.answer, 'bot');
    } catch (e) {
        appendMessage(`Error: ${e.message}`, 'bot');
    }
}

function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `chat-message ${sender}`;
    div.textContent = text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}
