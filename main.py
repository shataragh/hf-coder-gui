#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HF Coder GUI • Hugging Face Inference API (chat_completion)
Single-file, production-ready version with external Fluent-style icons.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, PhotoImage

import webbrowser

from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from pygments import lex
from pygments.lexers import (
    BashLexer,
    CLexer,
    HtmlLexer,
    JavascriptLexer,
    JsonLexer,
    PythonLexer,
)
from pygments.token import Token


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

LOG_DIR = Path.home() / ".hf_coder_gui"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "hf_coder_gui.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(threadName)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# External icon paths
# ---------------------------------------------------------------------------

ICON_DIR = Path(__file__).parent / "icons"
LINKEDIN_ICON_PATH = ICON_DIR / "linkedin.png"
GITHUB_ICON_PATH = ICON_DIR / "github.png"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelInfo:
    display_name: str
    model_id: str
    description: str


@dataclass(frozen=True)
class TemplateInfo:
    name: str
    description: str
    prompt: str


# ---------------------------------------------------------------------------
# Syntax highlighting text widget
# ---------------------------------------------------------------------------

class SyntaxHighlightingText(scrolledtext.ScrolledText):
    """Custom Text widget with real-time syntax highlighting using Pygments."""

    TAG_MAP: dict[Tuple[Token, ...], str] = {
        (Token.Keyword, Token.Keyword.Constant, Token.Keyword.Declaration, Token.Keyword.Namespace): "keyword",
        (Token.String, Token.String.Double, Token.String.Single, Token.String.Doc, Token.String.Heredoc): "string",
        (Token.Comment, Token.Comment.Single, Token.Comment.Multiline, Token.Comment.Special): "comment",
        (Token.Name.Function, Token.Name.Class, Token.Name.Decorator): "function",
        (Token.Number, Token.Number.Integer, Token.Number.Float, Token.Number.Hex, Token.Number.Oct): "number",
        (Token.Operator, Token.Operator.Word): "operator",
        (Token.Name.Builtin, Token.Name.Builtin.Pseudo, Token.Name.Exception): "builtin",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.configure(wrap=tk.NONE, font=("Consolas", 11), undo=True, maxundo=50)

        self.tag_configure("keyword", foreground="#569CD6", font=("Consolas", 11, "bold"))
        self.tag_configure("string", foreground="#CE9178")
        self.tag_configure("comment", foreground="#6A9955", font=("Consolas", 11, "italic"))
        self.tag_configure("function", foreground="#DCDCAA")
        self.tag_configure("number", foreground="#B5CEA8")
        self.tag_configure("operator", foreground="#D4D4D4")
        self.tag_configure("builtin", foreground="#4EC9B0")

        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<FocusOut>", lambda e: self.highlight_syntax())

    def _on_key_release(self, event=None):
        if event and event.keysym in ("Return", "Tab", "space", "BackSpace", "Delete", "colon", "semicolon"):
            self.highlight_syntax()

    def highlight_syntax(self):
        text = self.get("1.0", tk.END)
        if not text.strip():
            return

        for tag in self.tag_names():
            if tag not in ("sel",):
                self.tag_remove(tag, "1.0", tk.END)

        lexer = self._detect_lexer(text)
        self._apply_highlighting(text, lexer)

    def _detect_lexer(self, text: str):
        first = text[:300].lower()
        if any(k in first for k in ["import ", "def ", "class ", "print(", "__init__"]):
            return PythonLexer()
        if any(k in first for k in ["#!/bin/bash", "sudo ", "apt ", "curl "]):
            return BashLexer()
        if "#include" in first or "int main(" in first:
            return CLexer()
        if any(k in first for k in ["function ", "const ", "let ", "var ", "=>"]):
            return JavascriptLexer()
        if text.strip().startswith("{"):
            return JsonLexer()
        if "<html" in first:
            return HtmlLexer()
        return PythonLexer()

    def _apply_highlighting(self, text: str, lexer):
        idx = 0
        for token, content in lex(text, lexer):
            start = f"1.0+{idx}c"
            idx += len(content)
            end = f"1.0+{idx}c"
            tag = self._get_tag_for_token(token)
            if tag:
                try:
                    self.tag_add(tag, start, end)
                except tk.TclError:
                    pass

    def _get_tag_for_token(self, token):
        for token_types, tag_name in self.TAG_MAP.items():
            if token in token_types:
                return tag_name
        return None


# ---------------------------------------------------------------------------
# Main GUI application
# ---------------------------------------------------------------------------

class HuggingFaceCoderGUI:
    """Main application class for the HF Coder GUI."""

    MODELS: List[ModelInfo] = [
        ModelInfo("Qwen2.5-Coder-32B", "Qwen/Qwen2.5-Coder-32B-Instruct", "Excellent code generation"),
        ModelInfo("Qwen2.5-Coder-14B", "Qwen/Qwen2.5-Coder-14B-Instruct", "Fast and capable"),
        ModelInfo("DeepSeek-Coder-33B", "deepseek-ai/deepseek-coder-33b-instruct", "Strong coding model"),
        ModelInfo("CodeLlama-34B", "codellama/CodeLlama-34b-Instruct-hf", "Meta's code model"),
        ModelInfo("CodeLlama-13B", "codellama/CodeLlama-13b-Instruct-hf", "Faster variant"),
        ModelInfo("Mistral-7B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3", "General purpose"),
        ModelInfo("Zephyr-7B-β", "HuggingFaceH4/zephyr-7b-beta", "Fast and efficient"),
        ModelInfo("Phi-4", "microsoft/Phi-4", "Microsoft's latest"),
    ]

    TEMPLATES: List[TemplateInfo] = [
        TemplateInfo(
            "Python CLI Tool",
            "Create a Python CLI tool with argparse.",
            "Create a Python CLI tool with argparse that [describe functionality]. "
            "Include error handling and type hints.",
        ),
        TemplateInfo(
            "Bash Script",
            "Write a bash script with error checking.",
            "Write a bash script that [describe task]. Include comments and error checking.",
        ),
        TemplateInfo(
            "API Client",
            "Python class for REST API interaction.",
            "Create a Python class to interact with the [API name] REST API. "
            "Include authentication, error handling, and methods for GET/POST/PUT/DELETE.",
        ),
        TemplateInfo(
            "Data Processing",
            "Pandas-based data processing function.",
            "Write a Python function using pandas to [describe data task]. "
            "Handle missing values and edge cases.",
        ),
        TemplateInfo(
            "Web Scraper",
            "Python web scraper with rate limiting.",
            "Create a Python web scraper using requests and BeautifulSoup to extract [what data] "
            "from [website]. Include rate limiting.",
        ),
        TemplateInfo(
            "SQL Query",
            "SQL query with indexing suggestions.",
            "Write a SQL query to [describe query]. Include proper indexing suggestions.",
        ),
        TemplateInfo(
            "Unit Tests",
            "Generate pytest unit tests.",
            "Generate comprehensive pytest unit tests for this function: [paste function]",
        ),
        TemplateInfo(
            "Dockerfile",
            "Optimized Dockerfile with multi-stage builds.",
            "Create an optimized Dockerfile for a [language] application that [description]. "
            "Use multi-stage builds.",
        ),
        TemplateInfo(
            "Regex Pattern",
            "Regex pattern with explanation.",
            "Create a regex pattern to match [pattern description]. Include explanation and Python example.",
        ),
        TemplateInfo(
            "GitHub Action",
            "GitHub Actions CI/CD workflow.",
            "Create a GitHub Actions workflow to [describe CI/CD task]. Include proper triggers and caching.",
        ),
    ]

    CONFIG_FILE = LOG_DIR / "config.json"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("HF Coder GUI • Hugging Face Inference (API Activation Required)")
        self.root.geometry("1300x850")
        self.root.minsize(1000, 700)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client: Optional[InferenceClient] = None
        self.api_key: Optional[str] = None
        self.generation_active: bool = False
        self.stop_flag: bool = False
        self.response_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.current_model_id: str = self.MODELS[0].model_id

        self._load_config()
        self._build_styles()
        self._build_ui()

        self.on_model_change()
        self._start_queue_processor()

        self.root.after(100, lambda: self.prompt_text.focus_set())

    # ------------------------------------------------------------------ UI

    def _build_styles(self) -> None:
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure(
            "Status.TLabel",
            background="#1e1e1e",
            foreground="#d4d4d4",
            font=("Consolas", 9),
        )
        style.configure("Success.TLabel", foreground="#4EC9B0", font=("Segoe UI", 10, "bold"))
        style.configure("Error.TLabel", foreground="#F44747", font=("Segoe UI", 10, "bold"))
        style.configure("Warning.TLabel", foreground="#CE9178", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(
            main_frame,
            text="🤗 Hugging Face Coder",
            style="Title.TLabel",
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        self._create_activation_section(main_frame)
        self._create_config_section(main_frame)
        self._create_status_section(main_frame)
        self._create_prompt_section(main_frame)
        self._create_controls_section(main_frame)
        self._create_response_section(main_frame)
        self._create_footer(main_frame)

    def _create_activation_section(self, parent: ttk.Frame) -> None:
        activation_frame = ttk.LabelFrame(parent, text="🔐 API Activation", padding=15)
        activation_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 15))

        left_frame = ttk.Frame(activation_frame)
        left_frame.grid(row=0, column=0, sticky=tk.W)

        self.activation_status = ttk.Label(
            left_frame,
            text="🔴 API NOT ACTIVATED - Click 'Enter API Key' to start",
            style="Error.TLabel",
            font=("Segoe UI", 11, "bold"),
        )
        self.activation_status.pack(side=tk.LEFT, padx=(0, 20))

        self.activate_btn = ttk.Button(
            left_frame,
            text="🔑 Enter API Key",
            command=self.show_api_dialog,
            width=20,
        )
        self.activate_btn.pack(side=tk.LEFT, padx=5)

        self.test_btn = ttk.Button(
            left_frame,
            text="🔄 Test Connection",
            command=self.test_connection,
            width=20,
            state=tk.DISABLED,
        )
        self.test_btn.pack(side=tk.LEFT, padx=5)

        right_frame = ttk.Frame(activation_frame)
        right_frame.grid(row=0, column=1, sticky=tk.E, padx=(50, 0))

        ttk.Button(
            right_frame,
            text="❓ How to get API Key",
            command=self.show_help,
            width=20,
        ).pack(side=tk.LEFT)

    def _create_config_section(self, parent: ttk.Frame) -> None:
        config_frame = ttk.LabelFrame(parent, text="⚙️ Configuration", padding=10)
        config_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))

        ttk.Label(config_frame, text="Model:", style="Header.TLabel").grid(
            row=0, column=0, sticky=tk.W
        )

        model_names = [f"{m.display_name} - {m.description}" for m in self.MODELS]
        self.model_var = tk.StringVar(value=model_names[0])
        self.model_combo = ttk.Combobox(
            config_frame,
            textvariable=self.model_var,
            values=model_names,
            width=70,
            state="readonly",
        )
        self.model_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        params_frame = ttk.Frame(config_frame)
        params_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

        ttk.Label(params_frame, text="Max Tokens:").grid(row=0, column=0)
        self.max_tokens_var = tk.IntVar(value=2048)
        ttk.Spinbox(
            params_frame,
            from_=256,
            to=4096,
            increment=256,
            textvariable=self.max_tokens_var,
            width=8,
        ).grid(row=0, column=1, padx=(5, 20))

        ttk.Label(params_frame, text="Temperature:").grid(row=0, column=2)
        self.temp_var = tk.DoubleVar(value=0.3)
        ttk.Spinbox(
            params_frame,
            from_=0.1,
            to=1.0,
            increment=0.1,
            textvariable=self.temp_var,
            width=6,
        ).grid(row=0, column=3, padx=(5, 20))

        ttk.Label(params_frame, text="Top P:").grid(row=0, column=4)
        self.top_p_var = tk.DoubleVar(value=0.95)
        ttk.Spinbox(
            params_frame,
            from_=0.1,
            to=1.0,
            increment=0.05,
            textvariable=self.top_p_var,
            width=6,
        ).grid(row=0, column=5, padx=5)

        self.stream_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            params_frame,
            text="Stream response",
            variable=self.stream_var,
        ).grid(row=0, column=6, padx=(20, 0))

    def _create_status_section(self, parent: ttk.Frame) -> None:
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(0, 10))

        self.connection_status = ttk.Label(
            status_frame,
            text="⏳ Waiting for API activation...",
            style="Warning.TLabel",
        )
        self.connection_status.pack(side=tk.LEFT)

    def _create_prompt_section(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="💬 Prompt:", style="Header.TLabel").grid(
            row=4, column=0, sticky=tk.W, pady=(0, 5)
        )

        ttk.Button(
            parent,
            text="📋 Templates ▼",
            command=self.show_templates,
            width=15,
        ).grid(row=4, column=2, sticky=tk.E)

        prompt_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=2)
        prompt_frame.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky=(tk.N, tk.S, tk.E, tk.W),
            pady=(0, 15),
        )
        parent.rowconfigure(5, weight=0)

        self.prompt_text = scrolledtext.ScrolledText(
            prompt_frame,
            height=8,
            width=120,
            font=("Consolas", 11),
            wrap=tk.WORD,
            undo=True,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.prompt_text.bind("<Control-Return>", lambda e: self.generate_code())

    def _create_controls_section(self, parent: ttk.Frame) -> None:
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=6, column=0, columnspan=3, pady=(0, 15))

        self.generate_btn = ttk.Button(
            controls_frame,
            text="✨ Generate Code (Ctrl+Enter)",
            command=self.generate_code,
            width=30,
            state=tk.DISABLED,
        )
        self.generate_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(
            controls_frame,
            text="⏹ Stop",
            command=self.stop_generation,
            width=15,
            state=tk.DISABLED,
        )
        self.stop_btn.grid(row=0, column=1, padx=5)

        ttk.Button(
            controls_frame,
            text="📋 Copy",
            command=self.copy_response,
            width=15,
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            controls_frame,
            text="💾 Save As...",
            command=self.save_response,
            width=15,
        ).grid(row=0, column=3, padx=5)

        ttk.Button(
            controls_frame,
            text="🗑️ Clear",
            command=self.clear_all,
            width=15,
        ).grid(row=0, column=4, padx=5)

    def _create_response_section(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="📝 Response:", style="Header.TLabel").grid(
            row=7, column=0, sticky=tk.W, pady=(0, 5)
        )

        response_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=2)
        response_frame.grid(
            row=8,
            column=0,
            columnspan=3,
            sticky=(tk.N, tk.S, tk.E, tk.W),
            pady=(0, 10),
        )
        parent.rowconfigure(8, weight=1)
        parent.columnconfigure(0, weight=1)

        self.response_text = SyntaxHighlightingText(
            response_frame,
            height=25,
            width=120,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
            selectbackground="#264f78",
        )
        self.response_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.response_text.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Footer (LinkedIn + GitHub buttons)
    # ------------------------------------------------------------------

    def _create_footer(self, parent: ttk.Frame) -> None:
        status_bar = ttk.Frame(parent, style="Status.TLabel", relief=tk.SUNKEN)
        status_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.E, tk.W))

        self.status_var = tk.StringVar(value="🔴 Enter your Hugging Face API key to begin")
        status_label = ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel")
        status_label.pack(side=tk.LEFT, padx=10, pady=5)

        btn_frame = ttk.Frame(status_bar)
        btn_frame.pack(side=tk.RIGHT, padx=10)

        linkedin_img = None
        github_img = None

        try:
            linkedin_img = PhotoImage(file=str(LINKEDIN_ICON_PATH))
        except Exception as exc:
            logger.warning("Failed to load LinkedIn icon: %s", exc)

        try:
            github_img = PhotoImage(file=str(GITHUB_ICON_PATH))
        except Exception as exc:
            logger.warning("Failed to load GitHub icon: %s", exc)

        if linkedin_img is not None:
            linkedin_btn = ttk.Button(
                btn_frame,
                image=linkedin_img,
                command=lambda: webbrowser.open("https://www.linkedin.com/in/sir1/"),
                width=30
            )
            linkedin_btn.image = linkedin_img
            linkedin_btn.pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(
                btn_frame,
                text="LinkedIn",
                command=lambda: webbrowser.open("https://www.linkedin.com/in/sir1/"),
                width=10,
            ).pack(side=tk.LEFT, padx=5)

        if github_img is not None:
            github_btn = ttk.Button(
                btn_frame,
                image=github_img,
                command=lambda: webbrowser.open("https://github.com/shataragh/hf-coder-gui"),
                width=30
            )
            github_btn.image = github_img
            github_btn.pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(
                btn_frame,
                text="GitHub",
                command=lambda: webbrowser.open("https://github.com/shataragh/hf-coder-gui"),
                width=10,
            ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            parent,
            text="Shortcuts: Ctrl+Enter (Generate) | Ctrl+C (Copy) | Ctrl+S (Save) | Ctrl+L (Clear)",
            font=("Segoe UI", 9),
            foreground="#808080",
        ).grid(row=10, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        self.root.bind("<Control-s>", lambda e: self.save_response())
        self.root.bind("<Control-c>", lambda e: self.copy_response())
        self.root.bind("<Control-l>", lambda e: self.clear_all())

    # ------------------------------------------------------------------
    # Config load/save
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        if not self.CONFIG_FILE.exists():
            return
        try:
            with self.CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            model_id = data.get("model_id")
            if model_id:
                for m in self.MODELS:
                    if m.model_id == model_id:
                        self.current_model_id = model_id
                        break
            logger.info("Config loaded from %s", self.CONFIG_FILE)
        except Exception as exc:
            logger.warning("Failed to load config: %s", exc)

    def _save_config(self) -> None:
        data = {"model_id": self.current_model_id}
        try:
            with self.CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("Config saved to %s", self.CONFIG_FILE)
        except Exception as exc:
            logger.warning("Failed to save config: %s", exc)

    # ------------------------------------------------------------------
    # API Key Dialog
    # ------------------------------------------------------------------

    def show_api_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Hugging Face API Key Activation")
        dialog.geometry("550x300")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        ttk.Label(
            dialog,
            text="🔐 Enter Hugging Face API Key",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(20, 10))

        ttk.Label(
            dialog,
            text=(
                "Get your free API key at huggingface.co/settings/tokens\n"
                "Create a token with 'Read' permission."
            ),
            justify=tk.CENTER,
            foreground="#666666",
        ).pack(pady=5)

        key_frame = ttk.Frame(dialog)
        key_frame.pack(pady=15, padx=20, fill=tk.X)

        key_var = tk.StringVar()
        key_entry = ttk.Entry(
            key_frame,
            textvariable=key_var,
            width=50,
            show="•",
            font=("Consolas", 10),
        )
        key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        show_key_var = tk.BooleanVar(value=False)

        def toggle_show() -> None:
            key_entry.config(show="" if show_key_var.get() else "•")

        ttk.Checkbutton(
            key_frame,
            text="Show",
            variable=show_key_var,
            command=toggle_show,
        ).pack(side=tk.LEFT, padx=(10, 0))

        key_entry.focus_set()

        status_var = tk.StringVar(value="")
        status_label = ttk.Label(dialog, textvariable=status_var, foreground="#F44747", wraplength=500)
        status_label.pack(pady=10)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(0, 20))

        def activate() -> None:
            key = key_var.get().strip()
            if not key:
                status_var.set("❌ Please enter an API key")
                return
            if not key.startswith("hf_"):
                status_var.set("❌ Invalid format. HF keys start with 'hf_'")
                return

            status_var.set("⏳ Testing key...")
            dialog.update()

            try:
                client = InferenceClient(token=key)
                test_messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'OK'"},
                ]
                _ = client.chat_completion(
                    messages=test_messages,
                    model=self.current_model_id,
                    max_tokens=5,
                    temperature=0.1,
                )

                self.client = client
                self.api_key = key

                self.activation_status.config(
                    text="✅ API ACTIVATED - Ready to generate code",
                    style="Success.TLabel",
                )
                self.activate_btn.config(text="🔄 Change API Key")
                self.test_btn.config(state=tk.NORMAL)
                self.generate_btn.config(state=tk.NORMAL)
                self.connection_status.config(
                    text=f"✅ Connected to {self.current_model_id.split('/')[-1]}",
                    style="Success.TLabel",
                )
                self.status_var.set("✅ Ready! Enter a prompt and click Generate.")
                logger.info("API key activated successfully.")
                dialog.destroy()

            except Exception as exc:
                error = str(exc)
                logger.error("API key activation failed: %s", error)
                if "401" in error or "Unauthorized" in error:
                    status_var.set("❌ Invalid API key. Please check and try again.")
                elif "403" in error or "access" in error.lower():
                    status_var.set("⚠️ Valid key, but you need to accept the model license first.")
                elif "model" in error.lower() and "not found" in error.lower():
                    status_var.set("❌ Model not available. Try a different model.")
                elif "not supported" in error.lower():
                    status_var.set("❌ This model doesn't support chat. Try CodeLlama or Mistral.")
                elif "rate" in error.lower() or "429" in error:
                    status_var.set("⏳ Rate limited. Wait a moment and try again.")
                else:
                    status_var.set(f"❌ Error: {error[:120]}")

        ttk.Button(
            btn_frame,
            text="🚀 Activate & Test",
            command=activate,
            width=20,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        key_entry.bind("<Return>", lambda e: activate())

        ttk.Button(
            dialog,
            text="🌐 Open huggingface.co/settings/tokens",
            command=lambda: webbrowser.open("https://huggingface.co/settings/tokens"),
        ).pack(pady=(0, 10))

    # ------------------------------------------------------------------
    # Help dialog
    # ------------------------------------------------------------------

    def show_help(self) -> None:
        help_text = (
            "How to get your free Hugging Face API Key:\n\n"
            "1. Visit: https://huggingface.co/settings/tokens\n"
            "2. Click \"New token\"\n"
            "3. Name: \"coder-gui\" (or anything)\n"
            "4. Role: \"Read\" (sufficient for inference)\n"
            "5. Click \"Generate token\"\n"
            "6. Copy the key (starts with \"hf_\")\n"
            "7. Paste it in this app and click \"Activate\"\n\n"
            "⚠️ IMPORTANT: For some models, you must also:\n"
            "- Visit the model page (e.g., huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct)\n"
            "- Click \"Access repository\" or \"Accept and access\"\n"
            "- This is free and instant, just accepts the license terms\n\n"
            "💡 The API key is kept in memory only and never saved to disk."
        )
        messagebox.showinfo("How to Get API Key", help_text)

    # ------------------------------------------------------------------
    # Model switching
    # ------------------------------------------------------------------

    def on_model_change(self, event=None) -> None:
        selected = self.model_var.get()
        for m in self.MODELS:
            if m.display_name in selected:
                self.current_model_id = m.model_id
                break
        self._save_config()
        if self.client:
            self.connection_status.config(
                text=f"✅ Model: {self.current_model_id.split('/')[-1]}",
                style="Success.TLabel",
            )
        else:
            self.connection_status.config(
                text=f"ℹ️ Selected model: {self.current_model_id.split('/')[-1]} (activate API to use)",
                style="Warning.TLabel",
            )

    # ------------------------------------------------------------------
    # Templates popup
    # ------------------------------------------------------------------

    def show_templates(self) -> None:
        if not self.TEMPLATES:
            messagebox.showinfo("Templates", "No templates available.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Prompt Templates")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(True, True)

        ttk.Label(
            dialog,
            text="Prompt Templates",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(10, 5))

        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        templates_list = tk.Listbox(list_frame, height=10)
        templates_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=templates_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        templates_list.config(yscrollcommand=scrollbar.set)

        for t in self.TEMPLATES:
            templates_list.insert(tk.END, f"{t.name} — {t.description}")

        preview = scrolledtext.ScrolledText(
            dialog,
            height=6,
            wrap=tk.WORD,
            font=("Consolas", 10),
        )
        preview.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))
        preview.insert(tk.END, "Select a template to preview its prompt.")
        preview.config(state=tk.DISABLED)

        def on_select(event=None):
            idx = templates_list.curselection()
            if not idx:
                return
            t = self.TEMPLATES[idx[0]]
            preview.config(state=tk.NORMAL)
            preview.delete("1.0", tk.END)
            preview.insert(tk.END, t.prompt)
            preview.config(state=tk.DISABLED)

        templates_list.bind("<<ListboxSelect>>", on_select)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(0, 10))

        def apply_template():
            idx = templates_list.curselection()
            if not idx:
                messagebox.showwarning("No selection", "Please select a template.")
                return
            t = self.TEMPLATES[idx[0]]
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert(tk.END, t.prompt)
            dialog.destroy()
            self.prompt_text.focus_set()

        ttk.Button(
            btn_frame,
            text="Use Template",
            command=apply_template,
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Close",
            command=dialog.destroy,
            width=10,
        ).pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def test_connection(self) -> None:
        if not self.client:
            messagebox.showwarning("API Not Activated", "Please enter and activate your API key first.")
            return

        self.status_var.set("⏳ Testing connection...")
        self.root.update_idletasks()

        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'OK'"},
            ]
            _ = self.client.chat_completion(
                messages=messages,
                model=self.current_model_id,
                max_tokens=5,
                temperature=0.1,
            )
            self.connection_status.config(
                text=f"✅ Connected to {self.current_model_id.split('/')[-1]}",
                style="Success.TLabel",
            )
            self.status_var.set("✅ Connection test successful.")
            logger.info("Connection test successful.")
        except Exception as exc:
            error = str(exc)
            logger.error("Connection test failed: %s", error)
            self.connection_status.config(
                text="❌ Connection test failed",
                style="Error.TLabel",
            )
            self.status_var.set(f"❌ Connection error: {error[:120]}")
            messagebox.showerror("Connection Failed", f"Error while testing connection:\n\n{error}")

    # ------------------------------------------------------------------
    # Generation logic
    # ------------------------------------------------------------------

    def generate_code(self) -> None:
        if not self.client:
            messagebox.showwarning("API Not Activated", "Please enter and activate your API key first.")
            return

        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Empty Prompt", "Please enter a prompt before generating.")
            return

        if self.generation_active:
            return

        self.generation_active = True
        self.stop_flag = False
        self.generate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("⏳ Generating code...")
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.config(state=tk.DISABLED)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert coding assistant. Generate clean, well-structured code. "
                    "Prefer Python examples when ambiguous. Avoid excessive explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        max_tokens = int(self.max_tokens_var.get())
        temperature = float(self.temp_var.get())
        top_p = float(self.top_p_var.get())
        stream = bool(self.stream_var.get())

        def worker():
            try:
                if stream:
                    for chunk in self.client.chat_completion(
                        model=self.current_model_id,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        stream=True,
                    ):
                        if self.stop_flag:
                            break
                        delta = chunk.choices[0].delta
                        content = getattr(delta, "content", None)
                        if content:
                            self.response_queue.put(("append", content))
                    self.response_queue.put(("done", ""))
                else:
                    completion = self.client.chat_completion(
                        model=self.current_model_id,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        stream=False,
                    )
                    content = completion.choices[0].message["content"]
                    self.response_queue.put(("set", content))
                    self.response_queue.put(("done", ""))
            except HfHubHTTPError as exc:
                logger.error("HF HTTP error: %s", exc)
                self.response_queue.put(("error", str(exc)))
            except Exception as exc:
                logger.error("Generation error: %s", exc)
                self.response_queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True, name="HF-Generation-Thread").start()

    def stop_generation(self) -> None:
        if not self.generation_active:
            return
        self.stop_flag = True
        self.status_var.set("⏹ Stopping generation...")
        logger.info("Stop requested by user.")

    def _start_queue_processor(self) -> None:
        def process_queue():
            try:
                while True:
                    action, payload = self.response_queue.get_nowait()
                    if action == "append":
                        self._append_response(payload)
                    elif action == "set":
                        self._set_response(payload)
                    elif action == "error":
                        self._handle_error(payload)
                    elif action == "done":
                        self._finish_generation()
            except queue.Empty:
                pass
            self.root.after(50, process_queue)

        self.root.after(50, process_queue)

    def _append_response(self, text: str) -> None:
        self.response_text.config(state=tk.NORMAL)
        self.response_text.insert(tk.END, text)
        self.response_text.see(tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.response_text.highlight_syntax()

    def _set_response(self, text: str) -> None:
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert(tk.END, text)
        self.response_text.see(tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.response_text.highlight_syntax()

    def _handle_error(self, error: str) -> None:
        self.response_text.config(state=tk.NORMAL)
        self.response_text.insert(tk.END, f"\n\n[ERROR]\n{error}")
        self.response_text.config(state=tk.DISABLED)
        self.response_text.highlight_syntax()
        self.status_var.set(f"❌ Error during generation: {error[:120]}")
        self.generation_active = False
        self.stop_flag = False
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def _finish_generation(self) -> None:
        self.generation_active = False
        self.stop_flag = False
        self.generate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if "Error" not in self.status_var.get():
            self.status_var.set("✅ Generation finished.")
        logger.info("Generation finished.")

    # ------------------------------------------------------------------
    # Copy / Save / Clear
    # ------------------------------------------------------------------

    def copy_response(self) -> None:
        text = self.response_text.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("📋 Response copied to clipboard.")

    def save_response(self) -> None:
        text = self.response_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Nothing to Save", "There is no response to save.")
            return

        filetypes = [
            ("Python files", "*.py"),
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        ]
        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=filetypes,
            title="Save Response As",
        )
        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_var.set(f"💾 Saved to {os.path.basename(filename)}")
            logger.info("Response saved to %s", filename)
        except Exception as exc:
            logger.error("Failed to save response: %s", exc)
            messagebox.showerror("Save Failed", f"Could not save file:\n\n{exc}")

    def clear_all(self) -> None:
        self.prompt_text.delete("1.0", tk.END)
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.status_var.set("🗑️ Cleared prompt and response.")
        logger.info("Prompt and response cleared.")

    # ------------------------------------------------------------------
    # Window closing
    # ------------------------------------------------------------------

    def on_closing(self) -> None:
        if self.generation_active:
            if not messagebox.askyesno(
                "Quit",
                "Generation is still running. Do you really want to quit?",
            ):
                return
        logger.info("Application closing.")
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = HuggingFaceCoderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
