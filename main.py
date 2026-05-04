import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import json
import os
import webbrowser

# --- Конфигурация ---
GITHUB_API_URL = "https://api.github.com/users"
FAVORITES_FILE = "favorites.json"


def load_favorites():
    """Загружает избранных пользователей из JSON-файла."""
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_favorites(favorites):
    """Сохраняет избранных пользователей в JSON-файл."""
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=2, ensure_ascii=False)


class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("750x600")
        self.root.resizable(True, True)

        self.favorites = load_favorites()

        # --- Стили ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TEntry", padding=6)

        # --- Верхняя панель: поиск ---
        top_frame = ttk.Frame(root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="🔍 Введите имя пользователя GitHub:").pack(anchor=tk.W)
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(fill=tk.X, pady=(5, 0))

        self.search_entry = ttk.Entry(search_frame, font=("Segoe UI", 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self.search_user())

        self.search_btn = ttk.Button(search_frame, text="Поиск", command=self.search_user)
        self.search_btn.pack(side=tk.LEFT)

        # --- Таблица результатов ---
        result_frame = ttk.LabelFrame(root, text="📋 Результаты поиска", padding=8)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        columns = ("avatar", "login", "name", "public_repos", "followers", "url")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=8)

        self.tree.heading("avatar", text="Аватар")
        self.tree.heading("login", text="Логин")
        self.tree.heading("name", text="Имя")
        self.tree.heading("public_repos", text="Репозитории")
        self.tree.heading("followers", text="Подписчики")
        self.tree.heading("url", text="GitHub URL")

        self.tree.column("avatar", width=60, anchor=tk.CENTER)
        self.tree.column("login", width=120)
        self.tree.column("name", width=150)
        self.tree.column("public_repos", width=100, anchor=tk.CENTER)
        self.tree.column("followers", width=100, anchor=tk.CENTER)
        self.tree.column("url", width=200)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self.open_profile())

        # --- Кнопки действий ---
        btn_frame = ttk.Frame(root, padding=8)
        btn_frame.pack(fill=tk.X)

        self.add_fav_btn = ttk.Button(btn_frame, text="⭐ Добавить в избранное", command=self.add_to_favorites)
        self.add_fav_btn.pack(side=tk.LEFT, padx=5)

        self.open_btn = ttk.Button(btn_frame, text="🌐 Открыть профиль", command=self.open_profile)
        self.open_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="🗑️ Очистить результаты", command=self.clear_results)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.view_fav_btn = ttk.Button(btn_frame, text="📂 Избранные", command=self.show_favorites)
        self.view_fav_btn.pack(side=tk.RIGHT, padx=5)

        # --- Статус-бар ---
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=4)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.update_status()

    def search_user(self):
        """Поиск пользователя GitHub по логину."""
        username = self.search_entry.get().strip()

        if not username:
            messagebox.showwarning("Ошибка ввода", "⚠️ Поле поиска не должно быть пустым!\nВведите имя пользователя GitHub.")
            self.search_entry.focus_set()
            return

        self.status_var.set(f"🔍 Ищу пользователя '{username}'...")
        self.root.update_idletasks()

        try:
            url = f"{GITHUB_API_URL}/{username}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    self.display_user(data)
                    self.status_var.set(f"✅ Найден пользователь: {data.get('login')}")
                else:
                    messagebox.showerror("Ошибка API", f"GitHub API вернул ошибку: {response.status}")
                    self.status_var.set(f"❌ Ошибка API: {response.status}")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                messagebox.showerror("Не найден", f"❌ Пользователь '{username}' не найден на GitHub.")
                self.status_var.set("❌ Пользователь не найден")
            else:
                messagebox.showerror("Ошибка API", f"GitHub API вернул ошибку: {e.code}")
                self.status_var.set(f"❌ Ошибка API: {e.code}")
        except urllib.error.URLError:
            messagebox.showerror("Ошибка соединения", "🔌 Нет подключения к интернету. Проверьте сеть.")
            self.status_var.set("🔌 Ошибка соединения")
        except Exception as e:
            messagebox.showerror("Ошибка", f"⚠️ Произошла ошибка: {str(e)}")
            self.status_var.set("⚠️ Ошибка выполнения запроса")

    def display_user(self, data):
        """Отображает данные пользователя в таблице."""
        self.clear_results()

        login = data.get("login", "")
        name = data.get("name") or "(не указано)"
        repos = data.get("public_repos", 0)
        followers = data.get("followers", 0)
        profile_url = data.get("html_url", "")

        self.tree.insert("", tk.END, values=(
            "🖼️", login, name, repos, followers, profile_url
        ))

    def add_to_favorites(self):
        """Добавляет выбранного пользователя в избранное."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Нет выбора", "Сначала найдите пользователя и выберите его в таблице.")
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        login = values[1]

        for fav in self.favorites:
            if fav["login"] == login:
                messagebox.showinfo("Уже в избранном", f"⭐ Пользователь '{login}' уже в избранном!")
                return

        user_data = {
            "login": values[1],
            "name": values[2],
            "repos": values[3],
            "followers": values[4],
            "url": values[5]
        }

        self.favorites.append(user_data)
        save_favorites(self.favorites)
        self.update_status()
        messagebox.showinfo("Добавлено", f"⭐ Пользователь '{login}' добавлен в избранное!")

    def show_favorites(self):
        """Отображает окно со списком избранных пользователей."""
        if not self.favorites:
            messagebox.showinfo("Избранное пусто", "📂 У вас пока нет избранных пользователей.")
            return

        fav_window = tk.Toplevel(self.root)
        fav_window.title("⭐ Избранные пользователи")
        fav_window.geometry("600x400")
        fav_window.transient(self.root)
        fav_window.grab_set()

        ttk.Label(fav_window, text="⭐ Избранные пользователи GitHub", font=("Segoe UI", 14, "bold")).pack(pady=10)

        cols = ("login", "name", "repos", "followers")
        fav_tree = ttk.Treeview(fav_window, columns=cols, show="headings", height=10)
        fav_tree.heading("login", text="Логин")
        fav_tree.heading("name", text="Имя")
        fav_tree.heading("repos", text="Репозитории")
        fav_tree.heading("followers", text="Подписчики")

        fav_tree.column("login", width=150)
        fav_tree.column("name", width=200)
        fav_tree.column("repos", width=100, anchor=tk.CENTER)
        fav_tree.column("followers", width=100, anchor=tk.CENTER)

        for fav in self.favorites:
            fav_tree.insert("", tk.END, values=(
                fav["login"], fav["name"], fav["repos"], fav["followers"]
            ))

        fav_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def remove_favorite():
            selected = fav_tree.selection()
            if not selected:
                return
            item = fav_tree.item(selected[0])
            login = item["values"][0]
            self.favorites = [f for f in self.favorites if f["login"] != login]
            save_favorites(self.favorites)
            fav_tree.delete(selected[0])
            self.update_status()

        btn_frame = ttk.Frame(fav_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Button(btn_frame, text="❌ Удалить из избранного", command=remove_favorite).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=fav_window.destroy).pack(side=tk.RIGHT, padx=5)

    def open_profile(self):
        """Открывает профиль пользователя в браузере."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Нет выбора", "Выберите пользователя в таблице.")
            return

        item = self.tree.item(selected[0])
        url = item["values"][5]
        if url and url != "":
            webbrowser.open(url)
            self.status_var.set(f"🌐 Открыт профиль: {url}")

    def clear_results(self):
        """Очищает таблицу результатов."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def update_status(self):
        """Обновляет статус-бар с количеством избранных."""
        count = len(self.favorites)
        self.root.title(f"GitHub User Finder | ⭐ {count} в избранном")
        self.status_var.set(f"Готов | Избранных: {count}")


# --- Запуск приложения ---
if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
