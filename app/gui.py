import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .config import APP_NAME, OUTPUT_FILE
from .exporter import save_tracks
from .yandex import YandexMusicError, create_session, fetch_playlist


BG = "#0d0d0d"
PANEL = "#151515"
PANEL_LIGHT = "#1c1c1c"
BORDER = "#292929"

TEXT = "#eeeeee"
TEXT_SECONDARY = "#999999"
TEXT_MUTED = "#5f5f5f"

ACCENT = "#ffffff"
ACCENT_HOVER = "#dddddd"


class IconButton(tk.Frame):
    def __init__(
        self,
        master,
        icon,
        text,
        command,
        primary=False,
        **kwargs,
    ):
        super().__init__(
            master,
            bg=ACCENT if primary else PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0,
            cursor="hand2",
            **kwargs,
        )

        self.command = command
        self.primary = primary
        self.enabled = True

        self.normal_bg = ACCENT if primary else PANEL
        self.hover_bg = ACCENT_HOVER if primary else PANEL_LIGHT

        self.icon = tk.Canvas(
            self,
            width=18,
            height=18,
            bg=self.normal_bg,
            highlightthickness=0,
            bd=0,
        )
        self.icon.pack(
            side="left",
            padx=(12, 4),
            pady=9,
        )

        self.label = tk.Label(
            self,
            text=text,
            bg=self.normal_bg,
            fg="#111111" if primary else TEXT,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )
        self.label.pack(
            side="left",
            padx=(0, 13),
            pady=9,
        )

        self._draw_icon(icon)

        for widget in (self, self.icon, self.label):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)

    def _draw_icon(self, icon):
        color = "#111111" if self.primary else TEXT

        if icon == "download":
            self.icon.create_line(9, 3, 9, 11, fill=color, width=1.7)
            self.icon.create_line(5, 8, 9, 12, fill=color, width=1.7)
            self.icon.create_line(13, 8, 9, 12, fill=color, width=1.7)
            self.icon.create_line(4, 15, 14, 15, fill=color, width=1.7)

        elif icon == "file":
            self.icon.create_rectangle(4, 2, 13, 16, outline=color, width=1.4)
            self.icon.create_line(7, 6, 11, 6, fill=color, width=1.2)
            self.icon.create_line(7, 9, 11, 9, fill=color, width=1.2)
            self.icon.create_line(7, 12, 10, 12, fill=color, width=1.2)

        elif icon == "link":
            self.icon.create_oval(2, 6, 10, 13, outline=color, width=1.4)
            self.icon.create_oval(8, 5, 16, 12, outline=color, width=1.4)
            self.icon.create_line(6, 9, 12, 8, fill=color, width=1.4)

    def _on_enter(self, _event=None):
        if self.enabled:
            self._set_background(self.hover_bg)

    def _on_leave(self, _event=None):
        if self.enabled:
            self._set_background(self.normal_bg)

    def _on_click(self, _event=None):
        if self.enabled and self.command:
            self.command()

    def _set_background(self, color):
        self.configure(bg=color)
        self.icon.configure(bg=color)
        self.label.configure(bg=color)

    def set_enabled(self, enabled):
        self.enabled = enabled

        if enabled:
            self._set_background(self.normal_bg)
            self.label.configure(
                fg="#111111" if self.primary else TEXT,
                cursor="hand2",
            )
            self.configure(cursor="hand2")
        else:
            self._set_background("#111111")
            self.label.configure(
                fg="#454545",
                cursor="arrow",
            )
            self.configure(cursor="arrow")


class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("820x600")
        self.minsize(720, 520)
        self.configure(bg=BG)

        self.session = create_session()
        self.busy = False

        self.url = tk.StringVar()
        self.status = tk.StringVar(value="Готово")
        self.count = tk.StringVar(value="0 треков")

        self._setup_style()
        self._build()
        self._update_buttons()

    def _setup_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Dark.Vertical.TScrollbar",
            background=PANEL,
            troughcolor=PANEL,
            bordercolor=PANEL,
            arrowcolor=TEXT_MUTED,
            relief="flat",
        )

        style.configure(
            "Dark.Horizontal.TProgressbar",
            background=TEXT,
            troughcolor=PANEL,
            bordercolor=PANEL,
            lightcolor=TEXT,
            darkcolor=TEXT,
            thickness=4,
        )

    def _build(self):
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=28, pady=24)

        self._build_header(container)
        self._build_input(container)
        self._build_actions(container)
        self._build_progress(container)
        self._build_track_list(container)
        self._build_footer(container)

    def _build_header(self, parent):
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x", pady=(0, 22))

        logo = tk.Canvas(
            header,
            width=44,
            height=44,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        logo.pack(side="left", padx=(0, 12))

        logo.create_oval(
            3, 3, 41, 41,
            fill=PANEL_LIGHT,
            outline=BORDER,
            width=1,
        )
        logo.create_oval(
            15, 15, 29, 29,
            outline=TEXT,
            width=1.5,
        )
        logo.create_line(
            22, 10, 22, 22,
            fill=TEXT,
            width=1.5,
        )
        logo.create_line(
            22, 22, 28, 18,
            fill=TEXT,
            width=1.5,
        )

        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side="left")

        tk.Label(
            title_frame,
            text="Yandex Music Exporter",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 18),
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text="Экспорт треков из публичных плейлистов",
            bg=BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            header,
            textvariable=self.count,
            bg=BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9),
        ).pack(side="right", anchor="center")

    def _build_input(self, parent):
        tk.Label(
            parent,
            text="ССЫЛКА НА ПЛЕЙЛИСТ",
            bg=BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI Semibold", 9),
        ).pack(anchor="w", pady=(0, 7))

        input_frame = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        input_frame.pack(fill="x")

        link_icon = tk.Canvas(
            input_frame,
            width=36,
            height=38,
            bg=PANEL,
            highlightthickness=0,
            bd=0,
        )
        link_icon.pack(side="left")

        link_icon.create_oval(
            7, 13, 18, 22,
            outline=TEXT_SECONDARY,
            width=1.3,
        )
        link_icon.create_oval(
            15, 11, 27, 20,
            outline=TEXT_SECONDARY,
            width=1.3,
        )
        link_icon.create_line(
            12, 17, 22, 15,
            fill=TEXT_SECONDARY,
            width=1.3,
        )

        self.entry = tk.Entry(
            input_frame,
            textvariable=self.url,
            bg=PANEL,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground="#333333",
            selectforeground=TEXT,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
        )
        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8),
            ipady=9,
        )

        self.clear_button = IconButton(
            input_frame,
            icon="file",
            text="Очистить",
            command=self._clear,
            primary=False,
        )
        self.clear_button.pack(side="right", padx=5, pady=4)

        self.entry.bind(
            "<Return>",
            lambda _event: self._start(),
        )

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=BG)
        actions.pack(fill="x", pady=(14, 18))

        self.get_button = IconButton(
            actions,
            icon="download",
            text="Получить треки",
            command=self._start,
            primary=True,
        )
        self.get_button.pack(side="left")

        self.open_button = IconButton(
            actions,
            icon="file",
            text="Открыть tracks.txt",
            command=self._open_file,
            primary=False,
        )
        self.open_button.pack(side="left", padx=(8, 0))

    def _build_progress(self, parent):
        progress_frame = tk.Frame(parent, bg=BG)
        progress_frame.pack(fill="x", pady=(0, 14))

        status_row = tk.Frame(progress_frame, bg=BG)
        status_row.pack(fill="x", pady=(0, 7))

        tk.Label(
            status_row,
            textvariable=self.status,
            bg=BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9),
        ).pack(side="left")

        self.progress_value = tk.Label(
            status_row,
            text="",
            bg=BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI", 9),
        )
        self.progress_value.pack(side="right")

        self.progress = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            style="Dark.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x")

    def _build_track_list(self, parent):
        section = tk.Frame(parent, bg=BG)
        section.pack(fill="both", expand=True)

        title_row = tk.Frame(section, bg=BG)
        title_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            title_row,
            text="ТРЕКИ",
            bg=BG,
            fg=TEXT_SECONDARY,
            font=("Segoe UI Semibold", 9),
        ).pack(side="left")

        tk.Label(
            title_row,
            text="Двойной клик по строке для копирования",
            bg=BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        ).pack(side="right")

        list_frame = tk.Frame(
            section,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            bg=PANEL,
            fg=TEXT,
            selectbackground="#303030",
            selectforeground=TEXT,
            activestyle="none",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
            exportselection=False,
            selectmode="extended",
        )
        self.listbox.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(8, 0),
            pady=8,
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.listbox.yview,
            style="Dark.Vertical.TScrollbar",
        )
        scrollbar.pack(side="right", fill="y", padx=5, pady=5)

        self.listbox.configure(
            yscrollcommand=scrollbar.set,
        )

        self.listbox.bind(
            "<Double-Button-1>",
            self._copy_selected,
        )

    def _build_footer(self, parent):
        footer = tk.Frame(parent, bg=BG)
        footer.pack(fill="x", pady=(12, 0))

        tk.Label(
            footer,
            text=f"Файл: {OUTPUT_FILE}",
            bg=BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        ).pack(side="left")

        tk.Label(
            footer,
            text="UTF-8",
            bg=BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        ).pack(side="right")

    def _update_buttons(self):
        enabled = not self.busy
        self.get_button.set_enabled(enabled)
        self.clear_button.set_enabled(enabled)
        self.open_button.set_enabled(True)

    def _clear(self):
        if self.busy:
            return

        self.url.set("")
        self.status.set("Готово")
        self.count.set("0 треков")
        self.progress.configure(value=0)
        self.progress_value.configure(text="")
        self.listbox.delete(0, "end")
        self.entry.focus_set()

    def _start(self):
        if self.busy:
            return

        value = self.url.get().strip()

        if not value:
            messagebox.showwarning(
                APP_NAME,
                "Введите ссылку на публичный плейлист.",
            )
            self.entry.focus_set()
            return

        self.busy = True
        self._update_buttons()

        self.status.set("Получение плейлиста...")
        self.count.set("Загрузка...")
        self.progress_value.configure(text="")

        self.progress.configure(mode="indeterminate")
        self.progress.start(8)

        self.listbox.delete(0, "end")

        thread = threading.Thread(
            target=self._worker,
            args=(value,),
            daemon=True,
        )
        thread.start()

    def _worker(self, value):
        try:
            tracks = fetch_playlist(
                value,
                session=self.session,
                progress=self._progress,
            )

            save_tracks(tracks, OUTPUT_FILE)

            self.after(0, self._done, tracks)

        except (YandexMusicError, OSError) as exc:
            self.after(0, self._error, str(exc))

    def _progress(self, current, total):
        def update():
            if total:
                self.progress.configure(
                    mode="determinate",
                    maximum=total,
                    value=current,
                )
                self.count.set(f"{current} / {total}")
                self.progress_value.configure(
                    text=f"{current} / {total}",
                )
            else:
                self.count.set(f"{current} треков")

        self.after(0, update)

    def _done(self, tracks):
        self.busy = False
        self.progress.stop()
        self.progress.configure(
            mode="determinate",
            maximum=max(len(tracks), 1),
            value=len(tracks),
        )

        self.count.set(f"{len(tracks)} треков")
        self.progress_value.configure(text="100%")
        self.status.set(f"Сохранено в {OUTPUT_FILE}")

        self.listbox.delete(0, "end")

        if tracks:
            self.listbox.insert("end", *tracks)

        self._update_buttons()

        if not tracks:
            messagebox.showinfo(
                APP_NAME,
                "Плейлист пуст.",
            )

    def _error(self, text):
        self.busy = False
        self.progress.stop()
        self.progress.configure(
            mode="determinate",
            value=0,
        )

        self.count.set("0 треков")
        self.progress_value.configure(text="")
        self.status.set("Ошибка")
        self._update_buttons()

        messagebox.showerror(
            APP_NAME,
            text,
        )

    def _open_file(self):
        path = Path(OUTPUT_FILE).resolve()

        if not path.exists():
            messagebox.showinfo(
                APP_NAME,
                "Файл tracks.txt ещё не создан.",
            )
            return

        try:
            import os
            import subprocess
            import sys

            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])

        except OSError as exc:
            messagebox.showerror(
                APP_NAME,
                f"Не удалось открыть файл:\n{exc}",
            )

    def _copy_selected(self, _event=None):
        selected = self.listbox.curselection()

        if not selected:
            return

        text = "\n".join(
            self.listbox.get(index)
            for index in selected
        )

        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

        self.status.set(
            "Скопировано в буфер обмена"
        )


def run_gui():
    app = Application()
    app.mainloop()
