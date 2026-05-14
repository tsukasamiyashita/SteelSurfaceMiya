# app.py
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import numpy as np
from shapely.geometry import Polygon, Point
import trimesh
import ezdxf

# アプリケーションのバージョン
__version__ = "1.0.0"
APP_NAME = f"SteelSurfaceMiya-v{__version__}"

# カスタムテーマ設定
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# 鋼材のプリセットデータ (W, H, t1, t2)
PRESETS = {
    "H形鋼": {
        "100x100": (100, 100, 6, 8),
        "150x150": (150, 150, 7, 10),
        "200x200": (200, 200, 8, 12),
        "250x250": (250, 250, 9, 14),
        "300x300": (300, 300, 10, 15),
    },
    "I形鋼": {
        "100x75x5x8": (75, 100, 5, 8),
        "150x75x5.5x9.5": (75, 150, 5.5, 9.5),
        "200x100x7x10": (100, 200, 7, 10),
        "250x125x7.5x12.5": (125, 250, 7.5, 12.5),
    },
    "T形鋼": {
        "100x100x6x8": (100, 100, 6, 8),
        "150x150x7x10": (150, 150, 7, 10),
        "200x200x8x12": (200, 200, 8, 12),
    },
    "角形鋼管": {
        "50x50x1.6": (50, 50, 1.6, 1.6),
        "100x100x3.2": (100, 100, 3.2, 3.2),
        "150x150x4.5": (150, 150, 4.5, 4.5),
        "200x200x6.0": (200, 200, 6.0, 6.0),
    },
    "円形鋼管": {
        "48.6x2.3": (48.6, 48.6, 2.3, 2.3),
        "60.5x3.2": (60.5, 60.5, 3.2, 3.2),
        "114.3x4.5": (114.3, 114.3, 4.5, 4.5),
        "165.2x5.0": (165.2, 165.2, 5.0, 5.0),
    },
    "等辺山形鋼": {
        "50x50x6": (50, 50, 6, 6),
        "75x75x6": (75, 75, 6, 6),
        "100x100x10": (100, 100, 10, 10),
    },
    "不等辺山形鋼": {
        "75x50x6": (50, 75, 6, 6),
        "100x75x7": (75, 100, 7, 7),
        "150x90x9": (90, 150, 9, 9),
    },
    "溝形鋼": {
        "100x50x5x7.5": (50, 100, 5, 7.5),
        "150x75x6.5x10": (75, 150, 6.5, 10),
        "200x90x8x13.5": (90, 200, 8, 13.5),
    },
    "平鋼": {
        "50x6": (50, 0, 6, 0),
        "100x9": (100, 0, 9, 0),
        "150x12": (150, 0, 12, 0),
    },
    "角鋼": {
        "16x16": (16, 0, 0, 0),
        "25x25": (25, 0, 0, 0),
        "50x50": (50, 0, 0, 0),
    },
    "丸鋼": {
        "16": (16, 0, 0, 0),
        "25": (25, 0, 0, 0),
        "50": (50, 0, 0, 0),
    }
}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("800x500")
        self.minsize(800, 500)

        # UIの構築
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === 左ペイン：種類とサイズの選択 ===
        self.frame_left = ctk.CTkFrame(self)
        self.frame_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_left, text="1. 鋼材の選択", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))

        ctk.CTkLabel(self.frame_left, text="種類:").pack(anchor="w", padx=10)
        self.type_var = ctk.StringVar(value="H形鋼")
        self.combo_type = ctk.CTkComboBox(self.frame_left, variable=self.type_var, values=list(PRESETS.keys()), command=self.update_preset_list)
        self.combo_type.pack(fill="x", padx=10, pady=(0, 20))

        ctk.CTkLabel(self.frame_left, text="プリセットサイズ:").pack(anchor="w", padx=10)
        self.preset_var = ctk.StringVar()
        self.combo_preset = ctk.CTkComboBox(self.frame_left, variable=self.preset_var, command=self.apply_preset)
        self.combo_preset.pack(fill="x", padx=10, pady=(0, 20))

        # === 中央ペイン：寸法の詳細設定 ===
        self.frame_mid = ctk.CTkFrame(self)
        self.frame_mid.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_mid, text="2. 寸法設定 (mm)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))

        self.entries = {}
        fields = [
            ("width", "幅 (B) / 外径:"),
            ("height", "高さ (H):"),
            ("t1", "厚さ1 (t1 / ウェブ厚):"),
            ("t2", "厚さ2 (t2 / フランジ厚):")
        ]

        for key, label_text in fields:
            frame = ctk.CTkFrame(self.frame_mid, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(frame, width=100)
            entry.pack(side="right")
            self.entries[key] = entry

        # === 右ペイン：エクスポート設定 ===
        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_right, text="3. 出力設定", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))

        ctk.CTkLabel(self.frame_right, text="ファイル形式:").pack(anchor="w", padx=10)
        self.format_var = ctk.StringVar(value=".stl")
        self.combo_format = ctk.CTkComboBox(self.frame_right, variable=self.format_var, values=[".stl", ".obj", ".ply", ".dxf (2D断面)"])
        self.combo_format.pack(fill="x", padx=10, pady=(0, 30))

        self.btn_export = ctk.CTkButton(self.frame_right, text="ファイルを作成して保存", height=40, font=ctk.CTkFont(weight="bold"), command=self.export_file)
        self.btn_export.pack(fill="x", padx=10, pady=20)

        # READMEボタンを追加
        self.btn_readme = ctk.CTkButton(
            self.frame_right, 
            text="使い方を確認 (README)", 
            fg_color="transparent", 
            border_width=1, 
            text_color=("gray10", "gray90"),
            command=self.show_readme
        )
        self.btn_readme.pack(fill="x", padx=10, pady=(0, 20))

        # 初期化
        self.update_preset_list(self.type_var.get())

    def show_readme(self):
        readme_path = resource_path("README.md")
        content = "README.md が見つかりませんでした。"
        
        if os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"ファイルの読み込み中にエラーが発生しました:\n{str(e)}"
        
        # サブウィンドウの作成
        help_win = ctk.CTkToplevel(self)
        help_win.title("使い方 (README)")
        help_win.geometry("600x500")
        help_win.minsize(400, 300)
        
        # メインウィンドウを親として前面に保持する設定
        help_win.transient(self)
        
        # テキストボックスの配置
        textbox = ctk.CTkTextbox(help_win, wrap="word", font=ctk.CTkFont(size=13))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", content)
        textbox.configure(state="disabled")  # 読み取り専用に設定
        
        help_win.focus_force()

    def update_preset_list(self, choice):
        presets = list(PRESETS[choice].keys())
        self.combo_preset.configure(values=presets)
        self.combo_preset.set(presets[0])
        self.apply_preset(presets[0])

    def update_input_states(self, steel_type):
        # 一旦すべて有効化
        for key in ["width", "height", "t1", "t2"]:
            self.entries[key].configure(state="normal")

        # 種類に応じたフィールドの無効化
        if steel_type in ["円形鋼管", "丸鋼"]:
            self.entries["height"].configure(state="disabled")
            self.entries["t1"].configure(state="normal" if steel_type == "円形鋼管" else "disabled")
            self.entries["t2"].configure(state="disabled")
        elif steel_type == "角鋼":
            self.entries["height"].configure(state="disabled")
            self.entries["t1"].configure(state="disabled")
            self.entries["t2"].configure(state="disabled")
        elif steel_type == "平鋼":
            self.entries["height"].configure(state="disabled")
            self.entries["t2"].configure(state="disabled")

    def apply_preset(self, choice):
        steel_type = self.type_var.get()
        w, h, t1, t2 = PRESETS[steel_type][choice]
        
        for key in ["width", "height", "t1", "t2"]:
            self.entries[key].configure(state="normal")
            self.entries[key].delete(0, tk.END)
        
        self.entries["width"].insert(0, str(w))
        if h > 0: self.entries["height"].insert(0, str(h))
        if t1 > 0: self.entries["t1"].insert(0, str(t1))
        if t2 > 0: self.entries["t2"].insert(0, str(t2))

        self.update_input_states(steel_type)

    def get_dimensions(self):
        try:
            steel_type = self.type_var.get()
            w = float(self.entries["width"].get())
            
            h_str = self.entries["height"].get()
            h = float(h_str) if h_str else (w if steel_type in ["角形鋼管", "角鋼"] else 0.0)
            
            t1_str = self.entries["t1"].get()
            t1 = float(t1_str) if t1_str else 0.0
            
            t2_str = self.entries["t2"].get()
            t2 = float(t2_str) if t2_str else t1
            
            return w, h, t1, t2
        except ValueError:
            messagebox.showerror("エラー", "寸法には数値を入力してください。")
            return None

    def create_polygon(self, steel_type, w, h, t1, t2):
        if steel_type in ["H形鋼", "I形鋼"]:
            # 断面の中心を原点とする
            pts = [
                (-w/2, h/2), (w/2, h/2), (w/2, h/2-t2), (t1/2, h/2-t2),
                (t1/2, -h/2+t2), (w/2, -h/2+t2), (w/2, -h/2), (-w/2, -h/2),
                (-w/2, -h/2+t2), (-t1/2, -h/2+t2), (-t1/2, h/2-t2), (-w/2, h/2-t2)
            ]
            return Polygon(pts)
            
        elif steel_type == "T形鋼":
            pts = [
                (-w/2, h/2), (w/2, h/2), (w/2, h/2-t2), (t1/2, h/2-t2),
                (t1/2, -h/2), (-t1/2, -h/2), (-t1/2, h/2-t2), (-w/2, h/2-t2)
            ]
            return Polygon(pts)
        
        elif steel_type == "角形鋼管":
            outer = Polygon([(-w/2, h/2), (w/2, h/2), (w/2, -h/2), (-w/2, -h/2)])
            inner = Polygon([(-w/2+t1, h/2-t1), (w/2-t1, h/2-t1), (w/2-t1, -h/2+t1), (-w/2+t1, -h/2+t1)])
            return outer.difference(inner)

        elif steel_type == "円形鋼管":
            outer = Point(0, 0).buffer(w/2)
            inner = Point(0, 0).buffer(w/2 - t1)
            return outer.difference(inner)

        elif steel_type in ["等辺山形鋼", "不等辺山形鋼"]:
            pts = [
                (-w/2, h/2), (-w/2+t1, h/2), (-w/2+t1, -h/2+t2),
                (w/2, -h/2+t2), (w/2, -h/2), (-w/2, -h/2)
            ]
            return Polygon(pts)

        elif steel_type == "溝形鋼":
            pts = [
                (-w/2, h/2), (w/2, h/2), (w/2, h/2-t2), (-w/2+t1, h/2-t2),
                (-w/2+t1, -h/2+t2), (w/2, -h/2+t2), (w/2, -h/2), (-w/2, -h/2)
            ]
            return Polygon(pts)

        elif steel_type == "平鋼":
            pts = [
                (-w/2, t1/2), (w/2, t1/2), (w/2, -t1/2), (-w/2, -t1/2)
            ]
            return Polygon(pts)

        elif steel_type == "角鋼":
            pts = [
                (-w/2, w/2), (w/2, w/2), (w/2, -w/2), (-w/2, -w/2)
            ]
            return Polygon(pts)

        elif steel_type == "丸鋼":
            return Point(0, 0).buffer(w/2)

    def export_file(self):
        dims = self.get_dimensions()
        if not dims:
            return
        
        w, h, t1, t2 = dims
        steel_type = self.type_var.get()
        fmt = self.format_var.get()
        ext = fmt.split(" ")[0]

        # 種類に応じてデフォルトファイル名を変更
        if steel_type in ["丸鋼", "角鋼"]:
            name_part = f"{w}"
        elif steel_type == "平鋼":
            name_part = f"{w}x{t1}"
        else:
            name_part = f"{w}x{h}"

        file_path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{ext[1:].upper()} files", f"*{ext}")],
            initialfile=f"{steel_type}_{name_part}{ext}"
        )

        if not file_path:
            return

        try:
            poly = self.create_polygon(steel_type, w, h, t1, t2)

            if ext == ".dxf":
                self.export_dxf(poly, file_path)
            else:
                self.export_3d(poly, file_path, ext)
            
            messagebox.showinfo("成功", f"ファイルを保存しました:\n{file_path}")

        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの生成中にエラーが発生しました:\n{str(e)}")

    def export_dxf(self, poly, file_path):
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        def add_polygon_to_dxf(p):
            if p.is_empty:
                return
            coords = list(p.exterior.coords)
            msp.add_lwpolyline(coords, close=True)
            for interior in p.interiors:
                msp.add_lwpolyline(list(interior.coords), close=True)

        if poly.geom_type == 'MultiPolygon':
            for p in poly.geoms:
                add_polygon_to_dxf(p)
        else:
            add_polygon_to_dxf(poly)
            
        doc.saveas(file_path)

    def export_3d(self, poly, file_path, ext):
        # 2Dポリゴンを三角メッシュ化してサーフェスを作成
        vertices, faces = trimesh.creation.triangulate_polygon(poly)
        
        # 2Dの頂点データにZ=0を追加して3D座標に変換
        vertices_3d = np.column_stack((vertices, np.zeros(len(vertices))))
        
        # 面データのみのTrimeshを作成
        mesh = trimesh.Trimesh(vertices=vertices_3d, faces=faces)
        
        mesh.export(file_path)

if __name__ == "__main__":
    app = App()
    app.mainloop()