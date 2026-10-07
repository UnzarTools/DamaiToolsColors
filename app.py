"""
DAMAI TOOLS — Main Application UI
=================================
Minimalist Black & White with Lava Text, Profiles, Crosshair, and Tray.
"""

from __future__ import annotations

import os
import sys
import math
import threading
import tkinter as tk
import customtkinter as ctk

from engine import ColorEngine
from presets import PresetManager
from crosshair import CrosshairOverlay
import pystray
from PIL import Image, ImageDraw

# Minimalist Palette
BG_MAIN    = "#000000"
BG_PANEL   = "#060606"
TEXT_DIM   = "#444444"
TEXT_MAX   = "#ffffff"
FONT_MAIN  = "Segoe UI"

ctk.set_appearance_mode("dark")

def interpolate_color(val, max_val, min_hex, max_hex):
    ratio = min(abs(val) / max_val, 1.0) if max_val > 0 else 0
    ratio = ratio ** 0.4  
    
    def hex_to_rgb(hx):
        return tuple(int(hx[i:i+2], 16) for i in (1, 3, 5))
    def rgb_to_hex(rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        
    c1 = hex_to_rgb(min_hex)
    c2 = hex_to_rgb(max_hex)
    
    c = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
    return rgb_to_hex(c)

def get_lava_color(phase):
    phase = phase % 3.0
    if phase < 1.0:
        r, g, b = 255, 0, int(128 * phase)
    elif phase < 2.0:
        p = phase - 1.0
        r, g, b = int(255 - 115 * p), 0, int(128 + 127 * p)
    else:
        p = phase - 2.0
        r, g, b = int(140 + 115 * p), 0, int(255 - 255 * p)
        
    pulse = (math.sin(phase * math.pi * 6) + 1) / 2.0
    r = min(255, r + int(50 * pulse))
    g = min(255, g + int(30 * pulse))
    b = min(255, b + int(50 * pulse))
    return f"#{r:02x}{g:02x}{b:02x}"


class SliderRow(ctk.CTkFrame):
    def __init__(self, parent, label: str, from_: float, to: float, default: float = 0, steps: int = 200, fmt: str = "{:+.0f}", callback=None, width=380, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._cb = callback
        self._fmt = fmt
        self._def = default
        self._max_abs = max(abs(from_), abs(to))

        self._lbl = ctk.CTkLabel(self, text=label, font=(FONT_MAIN, 14, "bold"), text_color=TEXT_DIM, width=120, anchor="w")
        self._lbl.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self._sl = ctk.CTkSlider(
            self, from_=from_, to=to, number_of_steps=steps,
            progress_color=TEXT_DIM, button_color=TEXT_DIM, button_hover_color="#ffffff",
            fg_color="#181818", width=width, height=18,
            command=self._on_change
        )
        self._sl.set(default)
        self._sl.grid(row=0, column=1, padx=10, sticky="ew")

        self._val_lbl = ctk.CTkLabel(self, text=self._format(default), font=("Consolas", 15, "bold"), text_color=TEXT_DIM, width=65, anchor="e")
        self._val_lbl.grid(row=0, column=2, padx=(10, 0), sticky="e")
        self.columnconfigure(1, weight=1)

    def _format(self, v: float) -> str:
        try: return self._fmt.format(v)
        except: return f"{v:.2f}"

    def _update_color(self, v: float):
        color = interpolate_color(v, self._max_abs, TEXT_DIM, TEXT_MAX)
        self._lbl.configure(text_color=color)
        self._sl.configure(progress_color=color, button_color=color)
        self._val_lbl.configure(text_color=color)

    def _on_change(self, v: float):
        self._val_lbl.configure(text=self._format(v))
        self._update_color(v)
        if self._cb: self._cb(v)

    def get(self) -> float: return self._sl.get()
    def set(self, v: float):
        self._sl.set(v)
        self._on_change(v)


class DamaiToolApp:
    def __init__(self):
        self.engine = ColorEngine()
        self.presets = PresetManager()
        
        self._sliders = {}
        self._debounce = None
        self._hidden = False

        self.root = ctk.CTk()
        self.root.title("DAMAI TOOLS")
        self.root.geometry("950x650")
        self.root.minsize(850, 600)
        self.root.configure(fg_color=BG_MAIN)
        
        # Override close button to hide to tray
        self.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.root.bind("<Unmap>", self._on_unmap)
        
        try:
            ico = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
        except: pass

        self.engine.apply_preset({
            "brightness": 0, "contrast": 0, "exposure": 0.0, "gamma": 1.0,
            "saturation": 0, "vibrance": 0, "hue_shift": 0, "color_temp": 0
        })

        self.lava_phase = 0.0
        self.lava_speed = 0.15 
        
        self.title_intro = None
        self.title_main = None
        
        self.crosshair = CrosshairOverlay(self.root)
        self._tray = None

        self._build_intro()
        self._animate_lava()

    def _animate_lava(self):
        self.lava_phase += self.lava_speed
        color = get_lava_color(self.lava_phase)
        if self.title_intro and self.title_intro.winfo_exists():
            self.title_intro.configure(text_color=color)
        if self.title_main and self.title_main.winfo_exists():
            self.title_main.configure(text_color=color)
        self.root.after(30, self._animate_lava)

    def _build_intro(self):
        self.intro_frame = ctk.CTkFrame(self.root, fg_color=BG_MAIN)
        self.intro_frame.pack(fill="both", expand=True)

        self.title_intro = ctk.CTkLabel(
            self.intro_frame, text="DAMAI TOOLS", 
            font=(FONT_MAIN, 55, "bold"), text_color="#ff0000"
        )
        self.title_intro.place(relx=0.5, rely=0.5, anchor="center")
        self.root.after(1500, self._end_intro)

    def _end_intro(self):
        self.intro_frame.destroy()
        self.title_intro = None
        self._build_ui()
        self.lava_speed = 0.015

    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(self.root, fg_color=BG_MAIN)
        self.main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        self.title_main = ctk.CTkLabel(
            self.main_frame, text="DAMAI TOOLS", 
            font=(FONT_MAIN, 32, "bold"), text_color="#ff0000"
        )
        self.title_main.pack(anchor="nw", pady=(0, 20))

        self.tabs = ctk.CTkTabview(self.main_frame, fg_color=BG_PANEL, segmented_button_fg_color="#111", segmented_button_selected_color="#333", segmented_button_unselected_hover_color="#222")
        self.tabs.pack(fill="both", expand=True)
        
        self.tab_color = self.tabs.add("COLOR MOD")
        self.tab_crosshair = self.tabs.add("CROSSHAIR")

        self._build_color_tab()
        self._build_crosshair_tab()

    def _build_color_tab(self):
        left_panel = ctk.CTkFrame(self.tab_color, fg_color="transparent")
        left_panel.pack(side="left", fill="both", expand=True, padx=(10, 20), pady=20)

        right_panel = ctk.CTkFrame(self.tab_color, width=240, fg_color="#111111", corner_radius=12)
        right_panel.pack(side="right", fill="y", pady=20, padx=(0, 10))
        right_panel.pack_propagate(False)

        def mk(key, label, from_, to, default, fmt, steps=200):
            def cb(_v): self._schedule_apply()
            sr = SliderRow(left_panel, label=label, from_=from_, to=to, default=default, steps=steps, fmt=fmt, callback=cb, width=320)
            sr.pack(fill="x", pady=22)
            self._sliders[key] = sr

        mk("saturation", "Saturation", -100, 200, 0, "{:+.0f}", steps=300)
        mk("vibrance",   "Vibrance",   -100, 100, 0, "{:+.0f}")
        mk("hue_shift",  "Hue Shift",  -180, 180, 0, "{:+.0f}°", steps=360)
        mk("color_temp", "Color Temp", -100, 100, 0, "{:+.0f}")
        
        if not self.engine.mag_available:
            for key in ("saturation", "vibrance", "hue_shift", "color_temp"):
                self._sliders[key]._sl.configure(state="disabled")

        reset_btn = ctk.CTkButton(left_panel, text="RESET ALL", font=(FONT_MAIN, 12, "bold"), fg_color="transparent", text_color=TEXT_DIM, hover_color="#181818", border_width=1, border_color=TEXT_DIM, width=120, height=36, command=self._reset_all)
        reset_btn.pack(anchor="sw", side="bottom")

        for sr in self._sliders.values(): sr._update_color(0)

        ctk.CTkLabel(right_panel, text="PROFILES", font=(FONT_MAIN, 16, "bold"), text_color="#ffffff").pack(pady=(25, 10))
        self.profile_var = ctk.StringVar(value="DEFAULT")
        self.profile_menu = ctk.CTkOptionMenu(right_panel, variable=self.profile_var, values=self.presets.all_names(), font=(FONT_MAIN, 13, "bold"), fg_color="#222222", button_color="#333333", button_hover_color="#444444", command=self._load_profile)
        self.profile_menu.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(right_panel, text="CREATE NEW", font=(FONT_MAIN, 12, "bold"), text_color=TEXT_DIM).pack(pady=(40, 5))
        self.new_profile_entry = ctk.CTkEntry(right_panel, placeholder_text="Name...", font=(FONT_MAIN, 13), fg_color="#222222", border_color="#444444", text_color="#ffffff", height=36)
        self.new_profile_entry.pack(fill="x", padx=20, pady=5)

        save_btn = ctk.CTkButton(right_panel, text="SAVE", font=(FONT_MAIN, 12, "bold"), fg_color="#ffffff", text_color="#000000", hover_color="#dddddd", height=36, command=self._save_profile)
        save_btn.pack(fill="x", padx=20, pady=5)

        self.delete_btn = ctk.CTkButton(right_panel, text="DELETE", font=(FONT_MAIN, 12, "bold"), fg_color="transparent", text_color="#ff4444", hover_color="#330000", border_width=1, border_color="#ff4444", height=36, command=self._delete_profile)
        self.delete_btn.pack(fill="x", padx=20, pady=(40, 0))
        self._load_profile("DEFAULT")

    def _build_crosshair_tab(self):
        f = ctk.CTkFrame(self.tab_crosshair, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=40, pady=20)
        
        self.ch_active_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(f, text="Enable Crosshair", variable=self.ch_active_var, font=(FONT_MAIN, 16, "bold"), command=self._update_crosshair).pack(anchor="w", pady=(0, 20))
        
        # Type
        type_frame = ctk.CTkFrame(f, fg_color="transparent")
        type_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(type_frame, text="Style:", font=(FONT_MAIN, 14, "bold"), width=100, anchor="w").pack(side="left")
        self.ch_type_var = ctk.StringVar(value="+")
        for t in ["+", "x", "o"]:
            ctk.CTkRadioButton(type_frame, text=t, variable=self.ch_type_var, value=t, command=self._update_crosshair).pack(side="left", padx=10)
            
        # Size
        def cb_size(_v): self._update_crosshair()
        self.ch_size = SliderRow(f, label="Size", from_=2, to=50, default=15, steps=48, callback=cb_size, width=250)
        self.ch_size.pack(fill="x", pady=10)
        
        self.ch_out_size = SliderRow(f, label="Outline Size", from_=0, to=10, default=2, steps=10, callback=cb_size, width=250)
        self.ch_out_size.pack(fill="x", pady=10)
        
        # Colors
        def make_color_row(parent, label, default_hex):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=10)
            ctk.CTkLabel(row, text=label, font=(FONT_MAIN, 14, "bold"), width=120, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=100)
            entry.insert(0, default_hex)
            entry.pack(side="left", padx=10)
            entry.bind("<KeyRelease>", lambda e: self._update_crosshair())
            return entry
            
        self.ch_color_entry = make_color_row(f, "Color (Hex):", "#00ff00")
        self.ch_out_color_entry = make_color_row(f, "Outline (Hex):", "#000000")
        
        # Glow
        glow_frame = ctk.CTkFrame(f, fg_color="transparent")
        glow_frame.pack(fill="x", pady=10)
        self.ch_glow_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(glow_frame, text="Enable Glow", variable=self.ch_glow_var, font=(FONT_MAIN, 14, "bold"), command=self._update_crosshair).pack(side="left")
        
        self.ch_glow_color_entry = make_color_row(f, "Glow (Hex):", "#00ff00")
        
        self._update_crosshair()

    def _update_crosshair(self):
        try:
            self.crosshair.update_params(
                type=self.ch_type_var.get(),
                size=self.ch_size.get(),
                outline_size=self.ch_out_size.get(),
                color=self.ch_color_entry.get() or "#ffffff",
                outline_color=self.ch_out_color_entry.get() or "#000000",
                glow=self.ch_glow_var.get(),
                glow_color=self.ch_glow_color_entry.get() or "#ffffff"
            )
            self.crosshair.set_active(self.ch_active_var.get())
        except Exception as e:
            pass # ignore invalid hex inputs while typing

    # ... color profile methods ...
    def _load_profile(self, name):
        preset = self.presets.get(name)
        if preset is None: return
        self.profile_var.set(name)
        for key, sr in self._sliders.items():
            if key in preset: sr.set(preset[key])
        self._apply_sliders()
        if self.presets.is_builtin(name):
            self.delete_btn.configure(state="disabled", text_color=TEXT_DIM, border_color=TEXT_DIM)
        else:
            self.delete_btn.configure(state="normal", text_color="#ff4444", border_color="#ff4444")

    def _save_profile(self):
        name = self.new_profile_entry.get().strip().upper()
        if not name: return
        params = {k: round(sr.get(), 4) for k, sr in self._sliders.items()}
        if self.presets.save(name, params):
            self.profile_menu.configure(values=self.presets.all_names())
            self._load_profile(name)
            self.new_profile_entry.delete(0, 'end')

    def _delete_profile(self):
        name = self.profile_var.get()
        if self.presets.is_builtin(name): return
        self.presets.delete(name)
        self.profile_menu.configure(values=self.presets.all_names())
        self._load_profile("DEFAULT")

    def _reset_all(self):
        self._load_profile("DEFAULT")

    def _apply_sliders(self):
        params = {k: round(sr.get(), 4) for k, sr in self._sliders.items()}
        self.engine.update(**params)

    def _schedule_apply(self):
        if self._debounce: self.root.after_cancel(self._debounce)
        if not self._hidden: self._debounce = self.root.after(80, self._apply_sliders)

    # Tray handling
    def _on_unmap(self, event):
        if event.widget is self.root:
            self.root.after(60, self._check_iconic)

    def _check_iconic(self):
        try:
            if self.root.state() == "iconic":
                self._hide_to_tray()
        except: pass

    def _hide_to_tray(self):
        self._hidden = True
        self.root.withdraw()
        if self._tray is None:
            self._start_tray()

    def _show_from_tray(self):
        self.root.after(0, self._do_show)

    def _do_show(self):
        self._hidden = False
        self.root.deiconify()
        self.root.lift()

    def _start_tray(self):
        try:
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse([2, 2, 62, 62], fill=(255, 0, 128, 255))
            d.ellipse([12, 12, 52, 52], fill=(10, 10, 26, 255))
            d.ellipse([26, 26, 38, 38], fill=(255, 0, 128, 255))
            
            menu = pystray.Menu(
                pystray.MenuItem("Show Damai Tools", self._show_from_tray, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", lambda i, it: self.root.after(0, self._full_exit))
            )
            self._tray = pystray.Icon("DamaiTools", img, "Damai Tools", menu)
            threading.Thread(target=self._tray.run, daemon=True).start()
        except Exception as e:
            self._do_show()

    def _full_exit(self):
        self.engine.shutdown()
        if self._tray:
            try: self._tray.stop()
            except: pass
        self.root.destroy()

    def _on_close(self):
        # We override close to just hide to tray, so crosshair keeps running!
        self._hide_to_tray()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    DamaiToolApp().run()
