# gui/app.py
import os
import threading
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import filedialog, messagebox
from core import transcribe_audio, save_transcription


class TranscriberApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        # ⚙️ Настройка темы: ТЕМНАЯ, синие кнопки
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("Whisper Transcriber")
        self.geometry("600x580")
        self.minsize(500, 550)
        self.resizable(True, True)

        # Данные
        self.audio_path = None
        self.model_var = ctk.StringVar(value="turbo")  # по умолчанию turbo

        self.build_ui()

    def build_ui(self):
        # Основной фрейм — тёмный фон
        main_frame = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎙️ Whisper Transcriber",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(pady=(30, 5))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Перетащите аудиофайл или выберите вручную",
            font=ctk.CTkFont(size=13),
            text_color="#AAAAAA"
        )
        subtitle_label.pack(pady=(0, 20))

        # Строка с drop-зоной и кнопкой "Выбрать файл"
        row_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        row_frame.pack(pady=(0, 20), fill="x", padx=40)

        # Drop-зона — тёмная плашка
        self.drop_frame = ctk.CTkFrame(
            row_frame,
            width=300,
            height=100,
            corner_radius=8,
            fg_color="#222222",
            border_width=1,
            border_color="#404040"
        )
        self.drop_frame.pack(side="left", padx=(0, 20))
        self.drop_frame.pack_propagate(False)

        drop_inner = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        drop_inner.pack(expand=True)

        icon_label = ctk.CTkLabel(
            drop_inner,
            text="📁",
            font=ctk.CTkFont(size=20),
            text_color="#CCCCCC"
        )
        icon_label.pack()

        text_label = ctk.CTkLabel(
            drop_inner,
            text="Перетащите аудиофайл сюда\nПоддерживаемые форматы: MP3, WAV, M4A, FLAC, OGG",
            font=ctk.CTkFont(size=12),
            text_color="#CCCCCC",
            justify="center"
        )
        text_label.pack(pady=(5, 0))

        # Кнопка "Выбрать файл"
        select_btn = ctk.CTkButton(
            row_frame,
            text="📂 Выбрать файл",
            width=180,
            height=36,
            font=ctk.CTkFont(size=13),
            command=self.select_file
        )
        select_btn.pack(side="left")

        # Регистрация drag-and-drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind("<<Drop>>", self.on_drop)

        # Выбор модели — компактно
        model_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        model_frame.pack(pady=(0, 20))

        model_label = ctk.CTkLabel(
            model_frame,
            text="Модель Whisper:",
            font=ctk.CTkFont(size=13),
            text_color="#CCCCCC"
        )
        model_label.pack(side="left", padx=(0, 10))

        model_options = ["tiny", "base", "small", "medium", "large", "turbo"]
        model_menu = ctk.CTkOptionMenu(
            model_frame,
            variable=self.model_var,
            values=model_options,
            width=120,
            height=32,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13)
        )
        model_menu.pack(side="left")

        # Кнопка "Начать транскрибацию" — большая, внизу
        self.transcribe_btn = ctk.CTkButton(
            main_frame,
            text="▶️ Начать транскрибацию",
            width=220,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self.start_transcription
        )
        self.transcribe_btn.pack(pady=(30, 20))

        # Статусная метка — в самом низу
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA",
            wraplength=500,
            justify="center"
        )
        self.status_label.pack(pady=(0, 20))

        # Плашка с информацией о файле — будет создана при загрузке
        self.file_info_frame = None

    # --- Обработчики ---
    def on_drop(self, event):
        path = event.data.strip("{}")
        if self.is_audio(path):
            self.set_file(path)
        else:
            messagebox.showerror("Ошибка", "Неподдерживаемый формат файла!")

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Выберите аудиофайл",
            filetypes=[
                ("Аудиофайлы", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac"),
                ("Все файлы", "*.*")
            ]
        )
        if path and self.is_audio(path):
            self.set_file(path)

    def is_audio(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}

    def set_file(self, path):
        self.audio_path = path
        filename = os.path.basename(path)

        # Создаём/обновляем плашку с информацией о файле внизу
        if self.file_info_frame:
            self.file_info_frame.destroy()

        self.file_info_frame = ctk.CTkFrame(
            self.winfo_children()[0],  # main_frame
            width=480,
            height=100,
            corner_radius=8,
            fg_color="#222222",
            border_width=1,
            border_color="#404040"
        )
        self.file_info_frame.pack(pady=(0, 20), padx=40, fill="x")

        info_inner = ctk.CTkFrame(self.file_info_frame, fg_color="transparent")
        info_inner.pack(expand=True)

        check_icon = ctk.CTkLabel(
            info_inner,
            text="✅",
            font=ctk.CTkFont(size=24),
            text_color="#00D1B2"
        )
        check_icon.pack()

        file_label = ctk.CTkLabel(
            info_inner,
            text=f"Файл:\n{filename}",
            font=ctk.CTkFont(size=13),
            text_color="#00D1B2",
            justify="center"
        )
        file_label.pack(pady=(5, 0))

        self.transcribe_btn.configure(state="normal")

    def start_transcription(self):
        if not self.audio_path:
            return

        self.transcribe_btn.configure(state="disabled")
        self.update_status("⏳ Транскрибация запущена...", "#FFD166")

        thread = threading.Thread(target=self.run_transcription, daemon=True)
        thread.start()

    def run_transcription(self):
        model_name = self.model_var.get()
        result = transcribe_audio(self.audio_path, model_name)

        if result["success"]:
            try:
                output_path = save_transcription(result["text"], self.audio_path)
                self.update_status(f"✅ Готово!\nРезультат сохранён:\n{output_path}", "#06D6A0")
            except Exception as e:
                self.update_status(f"❌ Ошибка сохранения:\n{str(e)}", "#EF476F")
        else:
            self.update_status(f"❌ Ошибка транскрибации:\n{result['error']}", "#EF476F")

        self.transcribe_btn.configure(state="normal")

    def update_status(self, text, color):
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))