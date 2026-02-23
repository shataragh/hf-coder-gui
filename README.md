<div align="center">

# 🤗 HF Coder GUI  
### A Professional Desktop Interface for Hugging Face Code‑Generation Models

**Generate high‑quality code with top LLMs using a clean, powerful, and developer‑friendly desktop application.**

<br>

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg)

</div>

---

## 📘 Overview

**HF Coder GUI** is a modern, production‑ready desktop application built with Python and Tkinter.  
It provides a streamlined interface for interacting with Hugging Face’s `InferenceClient` using the `chat_completion` API — enabling developers to generate code efficiently using state‑of‑the‑art LLMs.

This tool is ideal for:

- Software engineers  
- Data scientists  
- AI researchers  
- Students learning to code  
- Anyone who wants a fast, reliable way to generate code with LLMs  

---

## ✨ Key Features

### 🔐 Secure API Activation
- Guided API key entry  
- Automatic validation & connection testing  
- API key stored **in memory only**  

### ⚙️ Advanced Model Configuration
- Curated list of high‑performance coding models:
  - Qwen2.5‑Coder (14B / 32B)
  - DeepSeek‑Coder‑33B
  - CodeLlama (13B / 34B)
  - Mistral‑7B‑Instruct
  - Zephyr‑7B‑β
  - Phi‑4
- Adjustable generation parameters:
  - Max tokens  
  - Temperature  
  - Top‑P  
  - Streaming mode  

### 🧠 Intelligent Code Generation
- Real‑time streaming output  
- Thread‑safe queue processing  
- Zero UI freezing  
- Clean, structured responses optimized for coding tasks  

### 🎨 Syntax‑Aware Output
Automatic syntax highlighting powered by **Pygments**, supporting:
- Python  
- Bash  
- C  
- JavaScript  
- JSON  
- HTML  

### 📋 Professional Prompt Templates
Instant templates for:
- CLI tools  
- Bash scripts  
- REST API clients  
- Data processing  
- Web scraping  
- SQL queries  
- Unit tests  
- Dockerfiles  
- Regex patterns  
- GitHub Actions  

### 🧰 Developer Utilities
- Copy output  
- Save to file  
- Clear prompt/output  
- Keyboard shortcuts  
- External Fluent‑style icons (LinkedIn + GitHub)

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/shataragh/hf-coder-gui.git
cd hf-coder-gui
