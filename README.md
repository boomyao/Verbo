# Verbo

> 我不想在学习前，先学一门语言

## Features

### 视频翻译配音

- [x] **高质量翻译**
- [x] **精准的音画同步**
- [x] **均衡的语速**
- [ ] **支持更多语言**
- [ ] **自动字幕生成与嵌入**
- [ ] **自动多人配音**
- [ ] **音色和口音匹配**

### Youtube 高阶字幕插件

- [x] **高质量字幕翻译**
- [x] **多人发言分割**
- [x] **逐句高亮**
- [ ] **移动端支持**
- [ ] **实时字幕配音**
- [ ] **AI 学习伴侣**
- [ ] **云端共享平台**

## Demo
<table>
<tr>
<td width="50%">

### 视频翻译配音
---
https://github.com/user-attachments/assets/548e7192-d80b-4051-b4de-90d03c244bd4

</td>
<td width="50%">

### 高阶字幕(多人发言)
---
https://github.com/user-attachments/assets/93a08ecf-f3c6-43c1-b703-e4776a6dd2ce

</td>
</tr>
</table>

## Getting Started

要开始使用 Verbo，请按照以下步骤操作：

1. 视频翻译配音
   ```sh
   python translate_video.py -i <video_file> -o <output_dir>
   ```
2. Youtube 高阶字幕
   ```sh
   # 启动服务
   python transcript_serve.py

   # 加载浏览器插件(transcript-extension)
   ```

## Concept

我们深信，可视化的力量不仅是信息的传递，更是对内容的补充。通过精心设计的配音与画面同步，我们确保节奏和视觉效果的完美协调，让观看体验更自然、更流畅。同时，我们的字幕扩展插件强调上下文的连贯性，因为我们相信，只有在连贯的阅读中，用户才能真正深入理解并从内容中受益。
