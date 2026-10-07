import tkinter as tk
import ctypes

def invert_hex(hex_col):
    hex_col = hex_col.lstrip('#')
    if len(hex_col) != 6: return "#000000"
    try:
        r, g, b = tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4))
        return f"#{255-r:02x}{255-g:02x}{255-b:02x}"
    except:
        return "#000000"

class CrosshairOverlay(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "black")
        self.config(bg="black")
        
        # Make it click-through
        self.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        
        w, h = 400, 400
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        
        self.canvas = tk.Canvas(self, width=w, height=h, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        self.active = False
        self.params = {
            "type": "+",
            "color": "#00ff00",
            "size": 15,
            "outline_size": 2,
            "outline_color": "#000000",
            "invert_outline": False,
            "glow": False,
            "glow_color": "#00ff00"
        }
        self.withdraw()
        
    def _draw(self):
        self.canvas.delete("all")
        if not self.active: return
        
        cx, cy = 200, 200
        size = int(self.params["size"])
        outline = int(self.params["outline_size"])
        c_color = self.params["color"]
        
        if self.params["invert_outline"]:
            o_color = invert_hex(c_color)
        else:
            o_color = self.params["outline_color"]
            
        glow = self.params["glow"]
        g_color = self.params["glow_color"]
        c_type = self.params["type"]
        
        def draw_shape(tag, color, width, offset=0):
            s = size + offset
            if c_type == "+":
                self.canvas.create_line(cx-s, cy, cx+s, cy, fill=color, width=width, tags=tag)
                self.canvas.create_line(cx, cy-s, cx, cy+s, fill=color, width=width, tags=tag)
            elif c_type == "x":
                self.canvas.create_line(cx-s, cy-s, cx+s, cy+s, fill=color, width=width, tags=tag)
                self.canvas.create_line(cx-s, cy+s, cx+s, cy-s, fill=color, width=width, tags=tag)
            elif c_type == "o":
                self.canvas.create_oval(cx-s, cy-s, cx+s, cy+s, outline=color, width=width, tags=tag)
                
        if glow:
            draw_shape("glow1", g_color, width=outline+6)
            draw_shape("glow2", g_color, width=outline+3)
            
        if outline > 0:
            draw_shape("outline", o_color, width=outline+2)
            
        draw_shape("core", c_color, width=2)
        
    def update_params(self, **kw):
        self.params.update(kw)
        self._draw()
        
    def set_active(self, state):
        self.active = state
        if state:
            self.deiconify()
        else:
            self.withdraw()
        self._draw()
