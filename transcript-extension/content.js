let transcriptViewer;
let transcriptControls;

const loadingIconCss = `
  .verbo-loading-icon {
    display: inline-block;
    width: 1em;
    height: 1em;
    border: 0.25em solid rgba(0, 0, 0, 0.2);
    border-top: 0.25em solid #000;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

class TranscriptViewer {
  constructor() {
    this.element = document.createElement('div');
    this.element.className = 'verbo-transcript-viewer';
    this.paragraphs = [];
    this.lastRenderedData = '';
    this.isUserScrolling = false;
  }

  async render() {
    if (this.isDataUnchanged()) {
      return;
    }

    const paragraphs = this.paragraphs;
    this.element.innerHTML = `
      <style>
        .verbo-transcript-viewer {
          width: 100%;
          height: ${paragraphs.length > 0 ? window.innerHeight - this.element.getBoundingClientRect().top : 0}px;
          overflow-y: auto;
          overscroll-behavior: contain;
        }
        .verbo-transcript-paragraph {
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding: 10px;
          font-size: 1.2rem;
          line-height: 1.5;
          cursor: pointer;
        }
        .verbo-transcript-paragraph:hover {
          background-color: #f0f0f0;
          transition: background-color 0.3s;
        }
        .verbo-time-range {
          color: #666;
          font-size: 0.9rem;
        }
        ${loadingIconCss}
        .verbo-sentence {
          transition: background-color 0.3s;
        }
        .verbo-sentence:hover {
          background-color: #e0e0e0;
        }
      </style>
      ${paragraphs.map((paragraph, index) => {
        const endTime = index < paragraphs.length - 1 ? paragraphs[index + 1].start : '';
        const timeRange = `${formatTime(paragraph.start)} - ${formatTime(endTime)}`;
        return `
          <div class="verbo-transcript-paragraph" data-start="${paragraph.start}" data-end="${endTime}">
            <p class="verbo-time-range">${timeRange}</p>
            <p class="verbo-original-text">
              ${(paragraph.lines || []).map(line => `
                <span class="verbo-sentence" data-start="${line.start}" data-end="${line.end}">${line.text}</span>
              `).join('')}
              ${!(paragraph.lines || []).length ? paragraph.text : ''}
            </p>
            ${paragraph.translated_text ?
              `<p class="verbo-translated-text">
                ${(paragraph.lines || []).map(line => `
                  <span class="verbo-translated-sentence" data-start="${line.start}" data-end="${line.end}">
                    ${line.translated_text || ''}
                  </span>
                `).join('')}
                ${!(paragraph.lines || []).length ? paragraph.translated_text : ''}
              </p>` :
              `<p class="verbo-loading-icon"></p>`
            }
          </div>`;
      }).join('')}
    `;

    this.lastRenderedData = JSON.stringify(this.paragraphs);
  }

  isDataUnchanged() {
    const currentData = JSON.stringify(this.paragraphs);
    return currentData === this.lastRenderedData;
  }

  setupEventListeners() {
    this.element.addEventListener('click', this.handleParagraphClick.bind(this));
    window.addEventListener('resize', this.updateHeight.bind(this));
    if (this.updateStyleInterval) {
      clearInterval(this.updateStyleInterval);
    }
    this.updateStyleInterval = setInterval(this.updateCurrentParagraphStyle.bind(this), 1000);
    
    let scrollTimeout;
    this.element.addEventListener('scroll', () => {
      this.isUserScrolling = true;
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        this.isUserScrolling = false;
      }, 2000);
    });
  }

  handleParagraphClick(event) {
    const paragraph = event.target.closest('.verbo-transcript-paragraph');
    if (paragraph) {
      const video = document.querySelector('video');
      if (video) {
        video.currentTime = parseFloat(paragraph.dataset.start);
      }
    }
  }

  updateHeight() {
    this.element.style.height = `${window.innerHeight - this.element.getBoundingClientRect().top}px`;
  }

  updateCurrentParagraphStyle() {
    const video = document.querySelector('video');
    if (video) {
      const currentTime = video.currentTime;
      const paragraphs = this.element.querySelectorAll('.verbo-transcript-paragraph');
      
      let activeParagraph = null;
      
      paragraphs.forEach(p => {
        const start = parseFloat(p.dataset.start);
        const end = parseFloat(p.dataset.end) || Infinity;
        
        const originalText = p.querySelector('.verbo-original-text');
        const translatedText = p.querySelector('.verbo-translated-text');
        
        if (currentTime >= start && currentTime < end) {
          originalText && (originalText.style.fontWeight = 'bold');
          translatedText && (translatedText.style.fontWeight = 'bold');
          activeParagraph = p;

          const sentences = p.querySelectorAll('.verbo-sentence, .verbo-translated-sentence');
          sentences.forEach(sentence => {
            const sentenceStart = parseFloat(sentence.dataset.start);
            const sentenceEnd = parseFloat(sentence.dataset.end);
            if (currentTime >= sentenceStart && currentTime < sentenceEnd) {
              sentence.style.backgroundColor = 'yellow';
            } else {
              sentence.style.backgroundColor = 'transparent';
            }
          });
        } else {
          originalText && (originalText.style.fontWeight = 'normal');
          translatedText && (translatedText.style.fontWeight = 'normal');
          
          // 清除非活动段落的句子高亮（包括翻译）
          const sentences = p.querySelectorAll('.verbo-sentence, .verbo-translated-sentence');
          sentences.forEach(sentence => {
            sentence.style.backgroundColor = 'transparent';
          });
        }
      });

      if (activeParagraph && !this.isUserScrolling) {
        this.scrollToActiveParagraph(activeParagraph);
      }
    }
  }

  scrollToActiveParagraph(activeParagraph) {
    const containerRect = this.element.getBoundingClientRect();
    const paragraphRect = activeParagraph.getBoundingClientRect();

    if (paragraphRect.top < containerRect.top || paragraphRect.bottom > containerRect.bottom) {
      const scrollTop = activeParagraph.offsetTop - (this.element.clientHeight / 2) + (activeParagraph.offsetHeight / 2);
      this.element.scrollTo({
        top: scrollTop,
        behavior: 'smooth'
      });
    }
  }

  updateTranscript(paragraphs) {
    this.paragraphs = paragraphs;
    this.render();
  }
}

class TranscriptControls {
  constructor() {
    this.element = document.createElement('div');
    this.element.className = 'verbo-transcript-controls';
    this.isLoading = false;
  }

  render() {
    const buttons = [
      { id: 'quick-translate', text: '快速翻译', action: 'translateTranscript' },
      { id: 'detailed-translate', text: '精细翻译', action: 'toggleTranscript' },
    ];

    this.element.innerHTML = `
      <style>
        .verbo-transcript-controls {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }
        .verbo-transcript-controls button {
          background-color: var(--yt-spec-badge-chip-background);
          color: var(--yt-spec-text-primary);
          border: none;
          border-radius: 18px;
          padding: 6px 12px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        .verbo-transcript-controls button:hover {
          background-color: var(--yt-spec-10-percent-layer);
        }
        .verbo-transcript-controls button:active {
          background-color: var(--yt-spec-15-percent-layer);
        }
      </style>
      ${buttons.map(button => `
        <button id="${button.id}">${button.text}</button>
      `).join('')}
    `;

    this.element.innerHTML += `
      <style>
        .verbo-transcript-controls button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      </style>
    `;
  }

  setupEventListeners() {
    this.element.querySelectorAll('button').forEach(button => {
      button.addEventListener('click', () => {
        if (!this.isLoading) {
          this.setLoading(true);
          const event = new CustomEvent(button.id, { bubbles: true });
          this.element.dispatchEvent(event);
        }
      });
    });
  }

  setLoading(isLoading) {
    this.isLoading = isLoading;
    const buttons = this.element.querySelectorAll('button');
    buttons.forEach(button => {
      button.disabled = isLoading;
      if (isLoading) {
        button.innerHTML += ' <span class="verbo-loading-icon"></span>';
      } else {
        button.innerHTML = button.innerHTML.replace(/ <span class="verbo-loading-icon"><\/span>/, '');
      }
    });
  }
}

function init() {
  const metadataContainer = document.querySelector('ytd-watch-metadata');
  transcriptControls = new TranscriptControls();
  metadataContainer.parentNode.insertBefore(transcriptControls.element, metadataContainer);
  transcriptControls.render();
  transcriptControls.setupEventListeners();

  transcriptViewer = new TranscriptViewer();
  metadataContainer.parentNode.insertBefore(transcriptViewer.element, transcriptControls.element);
  transcriptViewer.render();
  transcriptViewer.setupEventListeners();

  document.addEventListener('quick-translate', quickTranslate);
  document.addEventListener('detailed-translate', detailedTranslate);
}

const API_ENDPOINT = "http://localhost:5001"
const apiService = {
  getTranscript: async (video_id) => {
    const response = await fetch(`${API_ENDPOINT}/transcript/${video_id}`);
    return response.json();
  },
  getYtTranscript: async (video_id) => {
    const response = await fetch(`${API_ENDPOINT}/transcript_yt/${video_id}`);
    return response.json();
  },
  directTranslate: async (text) => {
    const response = await fetch(`${API_ENDPOINT}/translate/direct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    return response.json();
  }
}

function formatTime(seconds) {
  if (!seconds) return '';
  const date = new Date(0);
  date.setSeconds(seconds);
  return date.toISOString().substr(11, 8);
}

async function detailedTranslate() {
  try {
    const video_id = location.href.split("v=")[1].split("&")[0];
    const paragraphs = await apiService.getTranscript(video_id);
    transcriptViewer.updateTranscript(paragraphs);
  } finally {
    transcriptControls.setLoading(false);
  }
}

async function quickTranslate() {
  try {
    const batchSize = 10;
    const video_id = location.href.split("v=")[1].split("&")[0];
    const paragraphs = await apiService.getYtTranscript(video_id);
    transcriptViewer.updateTranscript(paragraphs);
    for (let i = 0; i < paragraphs.length; i += batchSize) {
      const batch = paragraphs.slice(i, i + batchSize);
      const promises = batch.map(paragraph => apiService.directTranslate(paragraph.text));
      const results = await Promise.all(promises);
      batch.forEach((paragraph, index) => {
        paragraph.translated_text = results[index].translated_text;
      });
      transcriptViewer.updateTranscript(paragraphs);
    }
  } finally {
    transcriptControls.setLoading(false);
  }
}

function checkForElement() {
  const targetElement = document.querySelector('ytd-watch-metadata');
  if (targetElement) {
    init();
  } else {
    setTimeout(checkForElement, 500);
  }
}

checkForElement();
