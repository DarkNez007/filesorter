import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

class FileCollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сборщик файлов по расширению")
        self.root.geometry("650x550")
        self.root.resizable(False, False)

        # Переменные
        self.src_dir = tk.StringVar()
        self.dst_dir = tk.StringVar()
        self.extension = tk.StringVar(value=".txt")
        self.action = tk.StringVar(value="copy")   # "copy" или "move"
        self.overwrite = tk.BooleanVar(value=False)

        # --- Виджеты ---
        # Исходная папка
        tk.Label(root, text="Исходная папка (поиск рекурсивно):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(root, textvariable=self.src_dir, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Обзор...", command=self.browse_src).grid(row=0, column=2, padx=5, pady=5)

        # Целевая папка
        tk.Label(root, text="Целевая папка:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(root, textvariable=self.dst_dir, width=50).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Обзор...", command=self.browse_dst).grid(row=1, column=2, padx=5, pady=5)

        # Расширение
        tk.Label(root, text="Расширение файлов (например, .txt, .pdf):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(root, textvariable=self.extension, width=20).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Действие (копировать/переместить)
        tk.Label(root, text="Действие:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        frame_action = tk.Frame(root)
        frame_action.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        tk.Radiobutton(frame_action, text="Копировать", variable=self.action, value="copy").pack(side="left", padx=5)
        tk.Radiobutton(frame_action, text="Переместить", variable=self.action, value="move").pack(side="left", padx=5)

        # Перезапись
        tk.Checkbutton(root, text="Перезаписывать существующие файлы", variable=self.overwrite).grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Кнопка запуска
        self.run_btn = tk.Button(root, text="Запустить сбор", command=self.collect_files, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.run_btn.grid(row=5, column=1, pady=15)

        # Лог (текстовое поле с прокруткой)
        tk.Label(root, text="Лог операций:").grid(row=6, column=0, sticky="nw", padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(root, width=75, height=20, state="normal")
        self.log_text.grid(row=7, column=0, columnspan=3, padx=10, pady=5)

        # Статусная строка
        self.status = tk.Label(root, text="Готов", bd=1, relief="sunken", anchor="w")
        self.status.grid(row=8, column=0, columnspan=3, sticky="we", padx=10, pady=5)

    def browse_src(self):
        dirname = filedialog.askdirectory(title="Выберите исходную папку")
        if dirname:
            self.src_dir.set(dirname)

    def browse_dst(self):
        dirname = filedialog.askdirectory(title="Выберите целевую папку")
        if dirname:
            self.dst_dir.set(dirname)

    def log(self, message):
        """Добавляет сообщение в лог и обновляет статус."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def set_status(self, text):
        self.status.config(text=text)
        self.root.update_idletasks()

    def collect_files(self):
        # Блокируем кнопку на время выполнения
        self.run_btn.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        self.set_status("Запуск...")

        # Получаем параметры
        src_dir = self.src_dir.get().strip()
        dst_dir = self.dst_dir.get().strip()
        ext = self.extension.get().strip()
        if not ext.startswith('.'):
            ext = '.' + ext
        action = self.action.get()
        overwrite = self.overwrite.get()

        # Проверки
        if not src_dir or not dst_dir:
            messagebox.showerror("Ошибка", "Выберите исходную и целевую папки.")
            self.run_btn.config(state="normal")
            return
        if not os.path.exists(src_dir):
            messagebox.showerror("Ошибка", f"Исходная папка не существует: {src_dir}")
            self.run_btn.config(state="normal")
            return
        if not os.path.exists(dst_dir):
            try:
                os.makedirs(dst_dir, exist_ok=True)
                self.log(f"Создана целевая папка: {dst_dir}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать целевую папку: {e}")
                self.run_btn.config(state="normal")
                return

        self.log(f"Поиск файлов с расширением '{ext}' в '{src_dir}' и подпапках...")
        self.set_status("Поиск файлов...")

        # Обход дерева
        found = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.lower().endswith(ext):
                    found.append(os.path.join(root, file))

        if not found:
            self.log("Файлы с заданным расширением не найдены.")
            self.set_status("Завершено (нет файлов)")
            self.run_btn.config(state="normal")
            return

        self.log(f"Найдено файлов: {len(found)}")
        self.set_status("Обработка...")

        processed = 0
        skipped = 0
        errors = 0

        for src_path in found:
            filename = os.path.basename(src_path)
            dst_path = os.path.join(dst_dir, filename)

            if os.path.exists(dst_path) and not overwrite:
                self.log(f"Пропуск (файл существует): {filename}")
                skipped += 1
                continue

            try:
                if action == "copy":
                    shutil.copy2(src_path, dst_path)
                    self.log(f"Копирован: {filename}")
                else:  # move
                    shutil.move(src_path, dst_path)
                    self.log(f"Перемещён: {filename}")
                processed += 1
            except Exception as e:
                self.log(f"ОШИБКА при обработке '{filename}': {e}")
                errors += 1

        # Итог
        self.log("\n--- Результат ---")
        self.log(f"Обработано: {processed}")
        self.log(f"Пропущено (существуют): {skipped}")
        self.log(f"Ошибок: {errors}")
        self.set_status(f"Готово. Обработано {processed} файлов.")
        self.run_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileCollectorApp(root)
    root.mainloop()