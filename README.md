<div align="center">

# 🤗 HF Coder GUI  
### A Professional Desktop Interface for Hugging Face Code‑Generation Models

**Generate high‑quality code with top LLMs using a clean, powerful, and developer‑friendly desktop application.**

<br>

<a href="https://www.python.org/downloads/" target="_blank">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
</a>
<a href="LICENSE" target="_blank">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</a>
<a href="#" target="_blank">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</a>
<a href="#" target="_blank">
  <img src="https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg" alt="Status">
</a>

<br><br>

<!-- ⚠️ Replace the src below with a permanent video URL (see note below) -->
<video width="640" controls poster="https://via.placeholder.com/640x360/0077b5/ffffff?text=HF+Coder+GUI+Demo">
  <source src="https://storage.filebin.net/filebin/622adbd92d6720a850a04de9408da539570704e9748c6ff4555e8489de177471?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=GK352fd2505074fc9dde7fd2cb%2F20260223%2Fhel1-dc4%2Fs3%2Faws4_request&X-Amz-Date=20260223T125145Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&response-cache-control=max-age%3D900&response-content-disposition=inline%3B%20filename%3D%22Agent.mp4%22&response-content-type=video%2Fmp4&x-id=GetObject&X-Amz-Signature=81982e127e798f61d3bc141de0e5dd162f72bf8294fc3c47e7909b044604b00e" type="video/mp4">
  Your browser does not support the video tag.
</video>

</div>

---

## 📘 Overview

**HF Coder GUI** is a modern, production‑ready desktop application built with Python and Tkinter.  
It provides a streamlined interface for interacting with Hugging Face's `InferenceClient` using the `chat_completion` API — enabling developers to generate code efficiently using state‑of‑the‑art LLMs.

This tool is ideal for:
- ✅ Software engineers  
- ✅ Data scientists  
- ✅ AI researchers  
- ✅ Students learning to code  
- ✅ Anyone who wants a fast, reliable way to generate code with LLMs  

---

## ✨ Key Features

### 🔐 Secure API Activation
- Guided API key entry with masked input  
- Automatic validation & connection testing  
- API key stored **in memory only** (never written to disk)  

### ⚙️ Advanced Model Configuration
- Curated list of high‑performance coding models:
  - `Qwen2.5‑Coder` (14B / 32B)  
  - `DeepSeek‑Coder‑33B`  
  - `CodeLlama` (13B / 34B)  
  - `Mistral‑7B‑Instruct`  
  - `Zephyr‑7B‑β`  
  - `Phi‑4`  
- Adjustable generation parameters:
  - Max tokens • Temperature • Top‑P • Streaming mode  

### 🧠 Intelligent Code Generation
- Real‑time streaming output with typewriter effect  
- Thread‑safe queue processing  
- Zero UI freezing during generation  
- Clean, structured responses optimized for coding tasks  

### 🎨 Syntax‑Aware Output
Automatic syntax highlighting powered by **Pygments**, supporting:
- `python` • `bash` • `c` • `javascript` • `json` • `html` • `sql` • `dockerfile`  

### 📋 Professional Prompt Templates
Instant templates for:
- CLI tools • Bash scripts • REST API clients  
- Data processing • Web scraping • SQL queries  
- Unit tests • Dockerfiles • Regex patterns • GitHub Actions  

### 🧰 Developer Utilities
- One‑click copy output • Save to file • Clear prompt/output  
- Keyboard shortcuts (`Ctrl+Enter` to generate, `Ctrl+L` to clear)  
- External Fluent‑style icons for LinkedIn + GitHub links  

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/shataragh/hf-coder-gui.git
cd hf-coder-gui
