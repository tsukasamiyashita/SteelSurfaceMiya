# app.py
import os
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
    "溝形鋼": {
        "100x50x5x7.5": (50, 100, 5, 7.5),
        "150x75x6.5x10": (75, 150, 6.5, 10),
        "200x90x8x13.5": (90, 200, 8, 13.5),
    }
}

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
            ("t2", "厚さ2 (t2 / フランジ厚):"),
            ("length", "長さ (L):")
        ]

        for key, label_text in fields:
            frame = ctk.CTkFrame(self.frame_mid, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(frame, width=100)
            entry.pack(side="right")
            self.entries[key] = entry

        # 初期値設定（長さのデフォルト）
        self.entries["length"].insert(0, "1000")

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

        # 初期化
        self.update_preset_list(self.type_var.get())

    def update_preset_list(self, choice):
        presets = list(PRESETS[choice].keys())
        self.combo_preset.configure(values=presets)
        self.combo_preset.set(presets[0])
        self.apply_preset(presets[0])

        # 種類に応じたフィールドの有効/無効化
        if choice == "円形鋼管":
            self.entries["height"].configure(state="disabled")
            self.entries["t2"].configure(state="disabled")
        else:
            self.entries["height"].configure(state="normal")
            self.entries["t2"].configure(state="normal")

    def apply_preset(self, choice):
        steel_type = self.type_var.get()
        w, h, t1, t2 = PRESETS[steel_type][choice]
        
        for key in ["width", "height", "t1", "t2"]:
            self.entries[key].configure(state="normal")
            self.entries[key].delete(0, tk.END)
        
        self.entries["width"].insert(0, str(w))
        self.entries["height"].insert(0, str(h))
        self.entries["t1"].insert(0, str(t1))
        self.entries["t2"].insert(0, str(t2))

        if steel_type == "円形鋼管":
            self.entries["height"].configure(state="disabled")
            self.entries["t2"].configure(state="disabled")

    def get_dimensions(self):
        try:
            w = float(self.entries["width"].get())
            h = float(self.entries["height"].get()) if self.entries["height"].get() else w
            t1 = float(self.entries["t1"].get())
            t2 = float(self.entries["t2"].get()) if self.entries["t2"].get() else t1
            length = float(self.entries["length"].get())
            return w, h, t1, t2, length
        except ValueError:
            messagebox.showerror("エラー", "寸法には数値を入力してください。")
            return None

    def create_polygon(self, steel_type, w, h, t1, t2):
        if steel_type == "H形鋼":
            # 断面の中心を原点とする
            pts = [
                (-w/2, h/2), (w/2, h/2), (w/2, h/2-t2), (t1/2, h/2-t2),
                (t1/2, -h/2+t2), (w/2, -h/2+t2), (w/2, -h/2), (-w/2, -h/2),
                (-w/2, -h/2+t2), (-t1/2, -h/2+t2), (-t1/2, h/2-t2), (-w/2, h/2-t2)
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

        elif steel_type == "等辺山形鋼":
            pts = [
                (-w/2, h/2), (-w/2+t1, h/2), (-w/2+t1, -h/2+t1),
                (w/2, -h/2+t1), (w/2, -h/2), (-w/2, -h/2)
            ]
            return Polygon(pts)

        elif steel_type == "溝形鋼":
            pts = [
                (-w/2, h/2), (w/2, h/2), (w/2, h/2-t2), (-w/2+t1, h/2-t2),
                (-w/2+t1, -h/2+t2), (w/2, -h/2+t2), (w/2, -h/2), (-w/2, -h/2)
            ]
            return Polygon(pts)

    def export_file(self):
        dims = self.get_dimensions()
        if not dims:
            return
        
        w, h, t1, t2, length = dims
        steel_type = self.type_var.get()
        fmt = self.format_var.get()
        ext = fmt.split(" ")[0]

        file_path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{ext[1:].upper()} files", f"*{ext}")],
            initialfile=f"{steel_type}_{w}x{h}_L{length}{ext}"
        )

        if not file_path:
            return

        try:
            poly = self.create_polygon(steel_type, w, h, t1, t2)

            if ext == ".dxf":
                self.export_dxf(poly, file_path)
            else:
                self.export_3d(poly, length, file_path, ext)
            
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

    def export_3d(self, poly, length, file_path, ext):
        # 2DポリゴンをZ方向に押し出して3Dメッシュを作成
        mesh = trimesh.creation.extrude_polygon(poly, height=length)
        # 向きや原点の調整 (押し出しはZ+方向に行われるため、中心を原点に合わせる)
        mesh.apply_translation([0, 0, -length/2])
        
        mesh.export(file_path)

if __name__ == "__main__":
    app = App()
    app.mainloop()