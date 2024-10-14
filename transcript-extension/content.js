function getTranscript(video_id) {
  return fetch(`http://localhost:5001/transcript/${video_id}`)
    .then(response => response.json())
    .then(paragraphs => {
      return paragraphs;
    });
}

async function replaceTranscript() {
  let transcriptContainer = document.getElementById('__transcript-container__');
  if (!transcriptContainer) {
    const button = document.getElementById('__transcript-button__');
    transcriptContainer = document.createElement('div');
    transcriptContainer.id = '__transcript-container__';
    transcriptContainer.style = "width: 100%; overflow-y: auto;";
    button.parentNode.insertBefore(transcriptContainer, button);
  }

  // 动态设置 transcriptContainer 的高度
  function setTranscriptContainerHeight() {
    const viewportHeight = window.innerHeight;
    const containerRect = transcriptContainer.getBoundingClientRect();
    const containerTop = containerRect.top;
    const newHeight = viewportHeight - containerTop;
    transcriptContainer.style.height = `${newHeight}px`;
  }

  // 初始设置高度
  setTranscriptContainerHeight();

  // 监听窗口大小变化，重新设置高度
  window.addEventListener('resize', setTranscriptContainerHeight);

  const video_id = location.href.split("v=")[1].split("&")[0];
  const paragraphs = await getTranscript(video_id);
  if (paragraphs) {
    transcriptContainer.innerHTML = paragraphs.map((paragraph, index) => {
      const endTime = index < paragraphs.length - 1 ? paragraphs[index + 1].start : '';
      const timeRange = `${formatTime(paragraph.start)} - ${formatTime(endTime)}`;
      return `
        <div class="transcript-paragraph" style="display: flex;flex-direction: column;gap: 10px;padding: 10px; font-size: 1.2rem; line-height: 1.5; cursor: pointer;" data-start="${paragraph.start}" data-end="${endTime}">
          <p style="color: #666; font-size: 0.9rem;">${timeRange}</p>
          <p class="original-text">${paragraph.text}</p>
          <p class="translated-text">${paragraph.translated_text}</p>
        </div>`;
    }).join('');
    
    // 添加点击事件监听器
    transcriptContainer.querySelectorAll('.transcript-paragraph').forEach(p => {
      p.addEventListener('click', () => {
        const video = document.querySelector('video');
        if (video) {
          video.currentTime = parseFloat(p.dataset.start);
        }
      });
    });
    
    // 添加定时器以更新当前段落的样式
    setInterval(updateCurrentParagraphStyle, 1000);
  }
}

function updateCurrentParagraphStyle() {
  const video = document.querySelector('video');
  if (video) {
    const currentTime = video.currentTime;
    const paragraphs = document.querySelectorAll('.transcript-paragraph');
    
    paragraphs.forEach(p => {
      const start = parseFloat(p.dataset.start);
      const end = parseFloat(p.dataset.end) || Infinity;
      
      if (currentTime >= start && currentTime < end) {
        p.querySelector('.original-text').style.fontWeight = 'bold';
        p.querySelector('.translated-text').style.fontWeight = 'bold';
      } else {
        p.querySelector('.original-text').style.fontWeight = 'normal';
        p.querySelector('.translated-text').style.fontWeight = 'normal';
      }
    });
  }
}

function init() {
  metadataContainer = document.querySelector('ytd-watch-metadata');
  // create a button
  const button = document.createElement('button');
  button.id = '__transcript-button__';
  button.innerHTML = 'View Transcript';
  button.addEventListener('click', () => {
    replaceTranscript();
  });
  // insert button before metadataContainer
  metadataContainer.parentNode.insertBefore(button, metadataContainer);
  
  // 添加样式
  const style = document.createElement('style');
  style.textContent = `
    .transcript-paragraph:hover {
      background-color: #f0f0f0;
      transition: background-color 0.3s;
    }
  `;
  document.head.appendChild(style);
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

// 添加这个辅助函数来格式化时间
function formatTime(seconds) {
  if (!seconds) return '';
  const date = new Date(0);
  date.setSeconds(seconds);
  return date.toISOString().substr(11, 8);
}
