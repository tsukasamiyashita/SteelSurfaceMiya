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

# 鋼材のプリセットデータ (W, H, t1, t2, r1, r2, taper)
PRESETS = {
    "H形鋼": {
        "100x100": (100, 100, 6, 8, 10, 0, 0),
        "150x150": (150, 150, 7, 10, 8, 0, 0),
        "200x200": (200, 200, 8, 12, 13, 0, 0),
        "250x250": (250, 250, 9, 14, 13, 0, 0),
        "300x300": (300, 300, 10, 15, 13, 0, 0),
    },
    "I形鋼": {
        "100x75x5x8": (75, 100, 5, 8, 7, 3.5, 16.67),
        "150x75x5.5x9.5": (75, 150, 5.5, 9.5, 9, 4.5, 16.67),
        "200x100x7x10": (100, 200, 7, 10, 10, 5, 16.67),
        "250x125x7.5x12.5": (125, 250, 7.5, 12.5, 12, 6, 16.67),
    },
    "T形鋼": {
        "100x100x6x8": (100, 100, 6, 8, 10, 0, 0),
        "150x150x7x10": (150, 150, 7, 10, 8, 0, 0),
        "200x200x8x12": (200, 200, 8, 12, 13, 0, 0),
    },
    "角形鋼管": {
        "50x50x1.6": (50, 50, 1.6, 1.6, 3.2, 0, 0),
        "100x100x3.2": (100, 100, 3.2, 3.2, 6.4, 0, 0),
        "150x150x4.5": (150, 150, 4.5, 4.5, 9.0, 0, 0),
        "200x200x6.0": (200, 200, 6.0, 6.0, 12.0, 0, 0),
    },
    "円形鋼管": {
        "48.6x2.3": (48.6, 48.6, 2.3, 2.3, 0, 0, 0),
        "60.5x3.2": (60.5, 60.5, 3.2, 3.2, 0, 0, 0),
        "114.3x4.5": (114.3, 114.3, 4.5, 4.5, 0, 0, 0),
        "165.2x5.0": (165.2, 165.2, 5.0, 5.0, 0, 0, 0),
    },
    "等辺山形鋼": {
        "50x50x6": (50, 50, 6, 6, 6.5, 4.5, 0),
        "75x75x6": (75, 75, 6, 6, 8.5, 6, 0),
        "100x100x10": (100, 100, 10, 10, 11, 7.5, 0),
    },
    "不等辺山形鋼": {
        "75x50x6": (50, 75, 6, 6, 6.5, 4.5, 0),
        "100x75x7": (75, 100, 7, 7, 8.5, 6, 0),
        "150x90x9": (90, 150, 9, 9, 11, 7.5, 0),
    },
    "溝形鋼": {
        "100x50x5x7.5": (50, 100, 5, 7.5, 8, 4, 5.0),
        "150x75x6.5x10": (75, 150, 6.5, 10, 10, 5, 5.0),
        "200x90x8x13.5": (90, 200, 8, 13.5, 14, 7, 5.0),
    },
    "平鋼": {
        "50x6": (50, 0, 6, 0, 0, 0, 0),
        "100x9": (100, 0, 9, 0, 0, 0, 0),
        "150x12": (150, 0, 12, 0, 0, 0, 0),
    },
    "角鋼": {
        "16x16": (16, 0, 0, 0, 0, 0, 0),
        "25x25": (25, 0, 0, 0, 0, 0, 0),
        "50x50": (50, 0, 0, 0, 0, 0, 0),
    },
    "丸鋼": {
        "16": (16, 0, 0, 0, 0, 0, 0),
        "25": (25, 0, 0, 0, 0, 0, 0),
        "50": (50, 0, 0, 0, 0, 0, 0),
    }
}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("850x650")
        self.minsize(850, 600)

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
            ("r1", "内R (r1 / フィレット):"),
            ("r2", "先端R (r2 / つま先):"),
            ("taper", "フランジ勾配 (%):")
        ]

        for key, label_text in fields:
            frame = ctk.CTkFrame(self.frame_mid, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(frame, text=label_text, width=150, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(frame, width=80)
            entry.pack(side="right")
            self.entries[key] = entry

        # === 右ペイン：エクスポート設定 ===
        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_right, text="3. 出力設定", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))

        ctk.CTkLabel(self.frame_right, text="ファイル形式:").pack(anchor="w", padx=10)
        self.format_var = ctk.StringVar(value=".stl")
        self.combo_format = ctk.CTkComboBox(self.frame_right, variable=self.format_var, values=[".stl", ".obj", ".ply", ".gltf", ".glb", ".off", ".dxf (2D断面)"])
        self.combo_format.pack(fill="x", padx=10, pady=(0, 10))

        # 拡張子の特徴について表示するボタンを追加
        self.btn_ext_info = ctk.CTkButton(
            self.frame_right,
            text="拡張子の特徴について",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self.show_extension_info
        )
        self.btn_ext_info.pack(fill="x", padx=10, pady=(0, 20))

        self.btn_export = ctk.CTkButton(self.frame_right, text="ファイルを作成して保存", height=40, font=ctk.CTkFont(weight="bold"), command=self.export_file)
        self.btn_export.pack(fill="x", padx=10, pady=(0, 20))

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

    def show_extension_info(self):
        content = """3D CADのファイル拡張子は、用途に合わせて「中間ファイル」「ポリゴンデータ」「ネイティブファイル」の3つに大別されます。それぞれの特徴は以下の通りです。

1. 中間ファイル（異なるCAD間のデータ連携用）
ソフトの垣根を越えて設計データをやり取りするための汎用フォーマットです。機械設計では主にこの形式を用いてデータを受け渡します。

・STEP (.step, .stp)
現在の主流規格（ISO準拠）です。ソリッド（中身の詰まった立体）とサーフェス（表面の面）の情報を保持でき、変換時の形状欠損が少ないため、最も信頼性が高いフォーマットです。

・Parasolid (.x_t, .x_b)
Siemens社の3Dカーネル（計算エンジン）に依存した形式です。SolidWorksやNXなど、同等のカーネルを採用しているCAD間での受け渡しにおいて、STEP以上の高い互換性と安定性を発揮します。

・IGES (.iges, .igs)
古くからある規格ですが、主にサーフェスデータとして変換されるため、別ソフトで開いた際に「面が剥がれる」「立体として認識されない」などの変換エラーが起きやすい傾向があります。現在はSTEPへの移行が進んでいます。

2. ポリゴン・メッシュデータ（3Dプリント・解析・CG用）
立体を細かい三角形（ポリゴン）の集合体として表現する形式です。表面の形状を表すのみであるため、CAD上での寸法変更や穴あけといった後からの再編集には不向きです。

・STL (.stl)
3Dプリンター用のデファクトスタンダードです。純粋な形状（メッシュ）データのみを保持し、色や材質の情報は持ちません。

・OBJ (.obj)
CGソフトや3Dスキャナーで広く利用されます。形状に加えて、色やテクスチャ（表面の質感）の情報を保持できます。

・PLY (.ply)
Polygon File Format。3Dスキャナーのデータ保存によく使われ、頂点ごとの色や透明度などのプロパティを格納するのに適しています。

・glTF / GLB (.gltf, .glb)
WebやAR/VR領域で標準的に使われる「3DモデルのJPEG」とも呼ばれる軽量フォーマットです。GLBはそのバイナリ（単一ファイル）形式です。

・OFF (.off)
オブジェクトファイルフォーマット。頂点とポリゴンの単純なリストで構成される、主に学術研究やジオメトリ処理で使われるシンプルな形式です。

・3MF (.3mf)
STLの次世代規格として策定された形式です。色、材質、内部のラティス（格子）構造などの詳細情報を1つのファイルに格納できます。

3. ネイティブファイル（特定ソフト専用）
各CADソフト固有の保存形式です。設計履歴（押し出し、カットなどの手順）や拘束条件を完全に保持できますが、原則として作成元のソフトでしか正確に編集できません。

・AutoCAD (.dwg, .dxf)
2D図面が主体ですが、3Dソリッドやメッシュデータを含めることも可能です。

・SolidWorks (.sldprt, .sldasm)
部品（パーツ）と組立（アセンブリ）で拡張子が分かれます。機械設備分野で高いシェアを持ちます。

・CATIA (.CATPart, .CATProduct)
曲面を多用する自動車や航空宇宙産業の標準フォーマットです。

・Fusion 360 (.f3d)
クラウドベースのCAD/CAM/CAEツール用形式です。

・Rhinoceros (.3dm)
プロダクトデザインなど、自由曲面の作成に特化したサーフェスモデラーの標準形式です。"""

        info_win = ctk.CTkToplevel(self)
        info_win.title("3D CADファイル拡張子の特徴")
        info_win.geometry("650x600")
        info_win.minsize(500, 400)
        info_win.transient(self)
        
        textbox = ctk.CTkTextbox(info_win, wrap="word", font=ctk.CTkFont(size=13))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", content)
        textbox.configure(state="disabled")
        info_win.focus_force()

    def show_readme(self):
        readme_path = resource_path("README.md")
        content = "README.md が見つかりませんでした。"
        
        if os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"ファイルの読み込み中にエラーが発生しました:\n{str(e)}"
        
        help_win = ctk.CTkToplevel(self)
        help_win.title("使い方 (README)")
        help_win.geometry("600x500")
        help_win.minsize(400, 300)
        help_win.transient(self)
        
        textbox = ctk.CTkTextbox(help_win, wrap="word", font=ctk.CTkFont(size=13))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", content)
        textbox.configure(state="disabled")
        help_win.focus_force()

    def update_preset_list(self, choice):
        presets = list(PRESETS[choice].keys())
        self.combo_preset.configure(values=presets)
        self.combo_preset.set(presets[0])
        self.apply_preset(presets[0])

    def update_input_states(self, steel_type):
        for key in ["width", "height", "t1", "t2", "r1", "r2", "taper"]:
            self.entries[key].configure(state="normal")

        if steel_type in ["円形鋼管", "丸鋼"]:
            for key in ["height", "t2", "r1", "r2", "taper"]:
                self.entries[key].configure(state="disabled")
            if steel_type == "丸鋼":
                self.entries["t1"].configure(state="disabled")
        elif steel_type in ["角鋼"]:
            for key in ["height", "t1", "t2", "r1", "r2", "taper"]:
                self.entries[key].configure(state="disabled")
        elif steel_type == "平鋼":
            for key in ["height", "t2", "r1", "r2", "taper"]:
                self.entries[key].configure(state="disabled")
        elif steel_type == "角形鋼管":
            for key in ["r2", "taper"]:
                self.entries[key].configure(state="disabled")

    def apply_preset(self, choice):
        steel_type = self.type_var.get()
        w, h, t1, t2, r1, r2, taper = PRESETS[steel_type][choice]
        
        for key in ["width", "height", "t1", "t2", "r1", "r2", "taper"]:
            self.entries[key].configure(state="normal")
            self.entries[key].delete(0, tk.END)
        
        self.entries["width"].insert(0, str(w))
        if h > 0: self.entries["height"].insert(0, str(h))
        if t1 > 0: self.entries["t1"].insert(0, str(t1))
        if t2 > 0: self.entries["t2"].insert(0, str(t2))
        self.entries["r1"].insert(0, str(r1) if r1 > 0 else "0")
        self.entries["r2"].insert(0, str(r2) if r2 > 0 else "0")
        self.entries["taper"].insert(0, str(taper) if taper > 0 else "0")

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
            
            r1_str = self.entries["r1"].get()
            r1 = float(r1_str) if r1_str else 0.0
            
            r2_str = self.entries["r2"].get()
            r2 = float(r2_str) if r2_str else 0.0
            
            taper_str = self.entries["taper"].get()
            taper = float(taper_str) if taper_str else 0.0
            
            return w, h, t1, t2, r1, r2, taper
        except ValueError:
            messagebox.showerror("エラー", "寸法には数値を入力してください。")
            return None

    def create_fillet_pts(self, cx, cy, r, start_angle, end_angle, steps=8):
        """ 円弧（フィレット）を構成する座標のリストを生成する """
        if r <= 0:
            return []
        pts = []
        for i in range(steps + 1):
            angle = np.radians(start_angle + (end_angle - start_angle) * i / steps)
            pts.append((cx + r * np.cos(angle), cy + r * np.sin(angle)))
        return pts

    def build_quadrant(self, w, h, t1, t2, r1, r2, S):
        """ 第一象限（右上）のテーパー・R付きフランジ輪郭を生成する """
        # S はテーパーの傾き。t2の基準位置はフランジ幅wの1/4（中心からの距離 w/4）とする。
        y0 = h/2 - t2 - S * (w/4)
        
        pts = [(0, h/2), (w/2, h/2)]
        theta = np.degrees(np.arctan(S))
        
        # 先端R (r2)
        if r2 > 0:
            cx2 = w/2 - r2
            cy2 = (S * cx2 + y0) + r2 * np.sqrt(S**2 + 1)
            arc2 = self.create_fillet_pts(cx2, cy2, r2, 360, 270 + theta)
            pts.extend(arc2)
        else:
            pts.append((w/2, S * (w/2) + y0))
            
        # 内R (r1)
        if r1 > 0:
            cx1 = t1/2 + r1
            cy1 = (S * cx1 + y0) - r1 * np.sqrt(S**2 + 1)
            arc1 = self.create_fillet_pts(cx1, cy1, r1, 90 + theta, 180)
            pts.extend(arc1)
        else:
            pts.append((t1/2, S * (t1/2) + y0))
            
        pts.append((t1/2, 0))
        return pts

    def create_polygon(self, steel_type, w, h, t1, t2, r1, r2, taper):
        S = taper / 100.0

        if steel_type in ["H形鋼", "I形鋼"]:
            q1 = self.build_quadrant(w, h, t1, t2, r1, r2, S)
            q4 = [(x, -y) for x, y in reversed(q1)]
            q3 = [(-x, -y) for x, y in q1]
            q2 = [(-x, y) for x, y in reversed(q1)]
            return Polygon(q1 + q4 + q3 + q2)
            
        elif steel_type == "T形鋼":
            q1 = self.build_quadrant(w, h, t1, t2, r1, r2, S)
            q2 = [(-x, y) for x, y in reversed(q1)]
            pts = q1 + [(t1/2, -h/2), (-t1/2, -h/2)] + q2
            return Polygon(pts)
            
        elif steel_type == "溝形鋼":
            # 溝形鋼は幅を2倍にして右半分(第一・第四象限)のみを利用する
            q1 = self.build_quadrant(w*2, h, t1*2, t2, r1, r2, S)
            q4 = [(x, -y) for x, y in reversed(q1)]
            # 取得した座標のXから w/2 を引いて、ウェブ左面を x = -w/2 に合わせる
            pts = [(x - w/2, y) for x, y in (q1 + q4)]
            # 左端の上下を直結
            pts.extend([(-w/2, -h/2), (-w/2, h/2)])
            return Polygon(pts)

        elif steel_type == "角形鋼管":
            if r1 > 0: # 角形鋼管のr1は外Rとして扱う
                outer_base = Polygon([(-w/2, h/2), (w/2, h/2), (w/2, -h/2), (-w/2, -h/2)])
                outer = outer_base.buffer(-r1, resolution=8).buffer(r1, resolution=8)
                
                inner_w = w - 2*t1
                inner_h = h - 2*t1
                if inner_w <= 0 or inner_h <= 0:
                    return outer
                
                inner_base = Polygon([(-inner_w/2, inner_h/2), (inner_w/2, inner_h/2), (inner_w/2, -inner_h/2), (-inner_w/2, -inner_h/2)])
                inner_r = r1 - t1
                if inner_r > 0:
                    inner = inner_base.buffer(-inner_r, resolution=8).buffer(inner_r, resolution=8)
                else:
                    inner = inner_base
                return outer.difference(inner)
            else:
                outer = Polygon([(-w/2, h/2), (w/2, h/2), (w/2, -h/2), (-w/2, -h/2)])
                inner = Polygon([(-w/2+t1, h/2-t1), (w/2-t1, h/2-t1), (w/2-t1, -h/2+t1), (-w/2+t1, -h/2+t1)])
                return outer.difference(inner)

        elif steel_type in ["等辺山形鋼", "不等辺山形鋼"]:
            pts = []
            pts.append((-w/2, -h/2))
            pts.append((w/2, -h/2))
            if r2 > 0:
                pts.append((w/2, -h/2 + t2 - r2))
                pts.extend(self.create_fillet_pts(w/2 - r2, -h/2 + t2 - r2, r2, 360, 90, steps=8))
            else:
                pts.append((w/2, -h/2 + t2))
                
            if r1 > 0:
                pts.append((-w/2 + t1 + r1, -h/2 + t2))
                pts.extend(self.create_fillet_pts(-w/2 + t1 + r1, -h/2 + t2 + r1, r1, 270, 180, steps=8))
            else:
                pts.append((-w/2 + t1, -h/2 + t2))
                
            if r2 > 0:
                pts.append((-w/2 + t1, h/2 - r2))
                pts.extend(self.create_fillet_pts(-w/2 + t1 - r2, h/2 - r2, r2, 0, 90, steps=8))
            else:
                pts.append((-w/2 + t1, h/2))
                
            pts.append((-w/2, h/2))
            return Polygon(pts)
            
        elif steel_type == "円形鋼管":
            outer = Point(0, 0).buffer(w/2)
            inner = Point(0, 0).buffer(w/2 - t1)
            return outer.difference(inner)

        elif steel_type == "平鋼":
            pts = [(-w/2, t1/2), (w/2, t1/2), (w/2, -t1/2), (-w/2, -t1/2)]
            return Polygon(pts)

        elif steel_type == "角鋼":
            pts = [(-w/2, w/2), (w/2, w/2), (w/2, -w/2), (-w/2, -w/2)]
            return Polygon(pts)

        elif steel_type == "丸鋼":
            return Point(0, 0).buffer(w/2)

    def export_file(self):
        dims = self.get_dimensions()
        if not dims:
            return
        
        w, h, t1, t2, r1, r2, taper = dims
        steel_type = self.type_var.get()
        fmt = self.format_var.get()
        ext = fmt.split(" ")[0]

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
            poly = self.create_polygon(steel_type, w, h, t1, t2, r1, r2, taper)

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
        vertices, faces = trimesh.creation.triangulate_polygon(poly)
        vertices_3d = np.column_stack((vertices, np.zeros(len(vertices))))
        mesh = trimesh.Trimesh(vertices=vertices_3d, faces=faces)
        mesh.export(file_path)

if __name__ == "__main__":
    app = App()
    app.mainloop()