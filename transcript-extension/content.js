function getTranscript(video_id) {
  fetch(`http://localhost:5000/transcript/${video_id}`)
    .then(response => response.json())
    .then(paragraphs => {
      return paragraphs;
    });
}

function replaceTranscript() {
  const transcriptContainer = document.querySelector('ytd-engagement-panel-section-list-renderer');
  
  if (transcriptContainer) {
    const video_id = location.href.split("v=")[1].split("&")[0];
    const paragraphs = getTranscript(video_id);
    if (paragraphs) {
      transcriptContainer.innerHTML = paragraphs.map(paragraph => `<p>${paragraph.translated_text}</p>`).join('');
    }
  }
}

let isTranscriptReplaced = false;

const observer = new MutationObserver(() => {
  if (!isTranscriptReplaced) {
    const transcriptContainer = document.querySelector('ytd-engagement-panel-section-list-renderer');
    if (transcriptContainer) {
      replaceTranscript();
      isTranscriptReplaced = true;
    }
  }
});

observer.observe(document.body, { childList: true, subtree: true });

// 添加一个函数来重置状态
function resetTranscriptState() {
  isTranscriptReplaced = false;
}

// 监听 URL 变化的改进实现
function listenForUrlChanges() {
  let lastUrl = location.href;

  // 监听 popstate 事件
  window.addEventListener('popstate', () => {
    const currentUrl = location.href;
    if (currentUrl !== lastUrl) {
      lastUrl = currentUrl;
      resetTranscriptState();
    }
  });

  // 拦截 history.pushState 和 history.replaceState
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;

  history.pushState = function() {
    originalPushState.apply(this, arguments);
    updateState();
  };

  history.replaceState = function() {
    originalReplaceState.apply(this, arguments);
    updateState();
  };

  function updateState() {
    const currentUrl = location.href;
    if (currentUrl !== lastUrl) {
      lastUrl = currentUrl;
      resetTranscriptState();
    }
  }
}

listenForUrlChanges();
