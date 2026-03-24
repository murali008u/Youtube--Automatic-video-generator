# YouTube Automation System

An automated system for generating and uploading YouTube Shorts using AI technologies. This project creates short-form content from historical and inspirational topics.

## 🚀 Features

- **AI-Powered Script Generation**: Uses Ollama LLM to create engaging educational scripts
- **Text-to-Speech**: Converts scripts to audio using Piper TTS
- **AI Image Generation**: Creates visuals using ComfyUI and Stable Diffusion
- **Video Rendering**: Combines audio and images into MP4 videos using MoviePy and FFmpeg
- **Thumbnail Generation**: Creates custom YouTube thumbnails
- **Automated Upload**: Publishes videos directly to YouTube via API
- **Database Management**: Tracks scripts, scenes, and videos in PostgreSQL

## 📋 Prerequisites

Before running this project, ensure you have the following installed:

### Required Software
- **Python 3.8+**
- **PostgreSQL** (running locally or remotely)
- **Git**
- **piper** (for audio tts)
- **FFmpeg** (for video processing)

### AI Services
- **Ollama** (for LLM script generation)
- **ComfyUI** (for AI image generation)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/murali008u/Youtube-Automatic-video-generator.git
cd youtube-automation
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Database
```bash
# Ensure PostgreSQL is running and create the database
python setup_db.py
```

### 4. Configure Environment Variables
Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/youtube_automation
DATABASE_PASSWORD= *****
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gpt-oss:120b-cloud  # or your preferred model

# YouTube API Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Optional: Custom paths
PIPER_EXECUTABLE=path/to/piper.exe
PIPER_VOICE=path/to/en_US-ryan-medium.onnx
```

## 🔧 Required Services Setup

### Ollama Setup
1. Download and install Ollama from [ollama.ai](https://ollama.ai)
2. Pull your preferred model:
```bash
ollama pull llama3:8b  # or your chosen model
```

### ComfyUI Setup
1. Download ComfyUI from [GitHub](https://github.com/comfyanonymous/ComfyUI)
2. Place it in `d:\ComfyUI-master` (or update the path in `orchestrator.py`)
3. Install required models

### Piper Setup
1. Download the Piper TTS executable for your OS from the [official releases](https://github.com/rhasspy/piper/releases)
2. Extract the contents into a `piper/` directory in the project root
3. Download a voice model (e.g., `en_US-ryan-medium.onnx` and its `.json` file) from the [Piper voices repository](https://huggingface.co/rhasspy/piper-voices/tree/main) and place them in the `piper/` directory
4. Update your `.env` file with the correct paths for `PIPER_EXECUTABLE` and `PIPER_VOICE`

### FFmpeg Setup
1. Download FFmpeg from the [official website](https://ffmpeg.org/download.html) or use a package manager (e.g., `winget install ffmpeg` on Windows, `brew install ffmpeg` on Mac, `sudo apt install ffmpeg` on Linux)
2. Ensure the `ffmpeg` executable is added to your system's PATH environment variable
3. Alternatively, extract FFmpeg binaries into an `ffmpeg_extracted/` folder in the project root

## 🎬 Running the Project
Before running the automation add your topics.txt file in the project root
1.good example (
The "Invisible" Chanakya
The Unconquered Fort
The Himalayan "Time Warp"
The "Lion of Maharashtra" ...... and so on
)
2.bad example(
1.The "Invisible" Chanakya
2.The Unconquered Fort
3.The Himalayan "Time Warp"
4.The "Lion of Maharashtra"
)


Run the complete automation pipeline:
```bash
python daily_job.py
```

Or use the batch file:
```bash
run_daily_automation.bat
```
Or add the batch file to windows task scheduler to run the automation daily without missing.

## 📁 Project Structure

```
youtube-automation/
├── core/
│   └── config.py          # Application configuration
├── db/
│   ├── database.py        # Database connection and models
│   └── models.py          # SQLAlchemy models
├── services/
│   ├── script_manager.py  # Script generation logic
│   ├── audio.py          # Text-to-speech processing
│   ├── images.py         # AI image generation
│   ├── video.py          # Video rendering
│   ├── thumbnail.py      # Thumbnail creation
│   ├── youtube_upload.py # YouTube API integration
│   └── topic_generator.py # Topic selection
├── piper/                # TTS models (ignored in git)
├── ffmpeg_extracted/     # FFmpeg binaries (ignored in git)
├── output/               # Generated content (ignored in git)
├── orchestrator.py       # Main automation pipeline
├── daily_job.py          # Daily automation runner
├── setup_db.py           # Database initialization
├── run_daily_automation.bat # Windows batch runner
├── topics.txt            # Topic database
└── requirements.txt      # Python dependencies
```

## ⚙️ Configuration

### YouTube API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials
5. Add your domain to authorized origins
6. Download `client_secrets.json` or use environment variables

### First Run Authentication
On first run, the system will:
1. Open a browser for YouTube authentication
2. Save tokens to `token.json` (automatically ignored by .gitignore)

## 🔍 Troubleshooting

### Common Issues

**Database Connection Error**
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Run `python setup_db.py` to create database

**Ollama Connection Error**
- Start Ollama service: `ollama serve`
- Verify model is pulled: `ollama list`
- Check `OLLAMA_HOST` in `.env`

**ComfyUI Not Found**
- Install ComfyUI in the expected path
- Update path in `orchestrator.py` if different
- Ensure ComfyUI is running on port 8188

**FFmpeg Not Found**
- The project includes FFmpeg binaries
- Or install system-wide FFmpeg
- Update paths in `services/audio.py` and `services/video.py`

**YouTube Upload Fails**
- Verify API credentials in `.env`
- Check `token.json` exists and is valid
- Ensure YouTube API is enabled

### Logs and Debugging
- Check console output for detailed error messages
- Generated files are saved in `output/script_{id}/`
- Videos are uploaded with `#shorts #history` and with some other tags if you want you can change that too services/youtube_upload.py

## 📝 Adding New Topics
Create `topics.txt` to add new educational topics, one per line.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any ideas you have to improve the project are **greatly appreciated**! 

If you have a suggestion or a new idea, please consider forking the repository and submitting a pull request to share it.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingIdea`)
3. Commit your changes (`git commit -m 'Add some AmazingIdea'`)
4. Test thoroughly
5. Push to the branch (`git push origin feature/AmazingIdea`)
6. Open a pull request

## 📄 License

This project is for educational purposes. Please respect YouTube's terms of service and content policies.

## ⚠️ Important Notes

- **API Limits**: Be aware of YouTube API quotas
- **Content Quality**: Review generated content before publishing
- **Resource Usage**: This system requires significant CPU/GPU resources
- **Costs**: AI services may incur costs if you are using the closed sources instead of open source (Ollama local, ComfyUI models, Piper TTS)
- **Legal**: Ensure compliance with content creation guidelines

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify all prerequisites are installed
3. Ensure environment variables are correct
4. Check that all AI services are running


For additional help, please check the code comments and documentation within each service file.
## Contact
If you have any questions or want to reach out, feel free to contact me at:
[murali008u@gmail.com].
