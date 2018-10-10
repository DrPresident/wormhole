from win32gui import *
import win32ui
from win32con import HALFTONE, SRCCOPY
from pynput.mouse import Listener
from sys import stderr
from tkinter import *
from PIL import Image, ImageTk
import numpy as np

import io


def to_win_pt(win, screen_pt):
    # negatives?
    rect = GetWindowRect(win)
    return (screen_pt[0] - rect[0], screen_pt[1] - rect[1])

mouse = Listener()
def next_click():

    # probably a better way, using just 'loc' didnt work through the thread
    class Payload:
        loc = None
    p = Payload()

    def on_click(x, y, button, pressed):
        if pressed:
            p.loc = (x,y)
            print('Click', p.loc)
            return False
        # else continue
        return True

    # use to draw rectangle around view
    def on_move(event):
        pass

    with Listener(on_click=on_click) as l:
        l.join()

    return p.loc

def to_rect(p0,p1):
    x = min(p0[0],p1[0])
    y = min(p0[1],p1[1])
    w = max(p0[0],p1[0]) - x
    h = max(p0[1],p1[1]) - y

    return (x,y,w,h)

i = [1]
def get_worm_hole(win, rect=None):

    win_dc = GetWindowDC(win)
    SetStretchBltMode(win_dc,HALFTONE)

    target_dc = win32ui.CreateDCFromHandle(win_dc)

    #w_hole = target_dc.CreateCompatibleDC()

    rect = rect if rect else GetClientRect(win)
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(target_dc,*rect[2:])

    #w_hole.SelectObject(bmp)
    #w_hole.StretchBlt((0,0), rect[2:], target_dc, rect[:2],rect[2:], SRCCOPY)

    image = Image.frombuffer(
            'RGB', 
            rect[2:],
            bmp.GetBitmapBits(True),
            'raw', 'BGRX', 0, 1)
    '''
    image = Image.fromarray(np.asarray(bmp.GetBitmapBits(False)),'RGBA')
    image = Image.frombytes("RGBA", rect[2:], bmp.GetBitmapBits(True))
    '''

    if i[0]:
        #image.show()
        i[0] -= 1

    return ImageTk.PhotoImage(image)


print('Select opposing corners of your view')
# window selected based on first click
_box = [-1, -1, -1, -1]
_listener = None
overlay = None
def _draw_box(w,h):
    if overlay:
        _box[2:] = (x,y)
        return True
    else:
        return False

def start_box(x,y):
    _box[:2] = (x,y)
    overlay = Tk()
    overlay.title('Overlay')
    overlay.attributes('-alpha',0.1)
    overlay.geometry("0x0+%d+%d" % (overlay.winfo_screenwidth(), overlay.winfo_screenheight()))
    overlay.lift()
    
    '''
    canvas = Canvas(overlay, width=200, height=200)#width=overlay.winfo_screenwidth(), height=overlay.winfo_screenheight)
    canvas.pack()
    canvas.create_rectangle(*_box, fill='gold')
    '''

    _listener = Listener(on_move=_draw_box)

def stop_box():
    if overlay:
        overlay.destroy()
    _box = [-1,-1,-1,-1]
    if _listener:
        _listener.join()

# create wormhole
r0 = next_click()
start_box(*r0)
r1 = next_click()
stop_box()

# need to validate both clicks are in the same window
start_box(0,0)

target_win = WindowFromPoint(r0)
target_title = GetWindowText(target_win)
target_rect = GetWindowRect(target_win)

rel0 = to_win_pt(target_win, r0)
rel1 = to_win_pt(target_win, r1)

worm_hole = list(to_rect(rel0,rel1))

print('Targeting', target_title)
print('Worm Hole', worm_hole)
print()

worm_view = Tk()

label = Label(worm_view)
label.pack()

def on_config(event):
    # more sophisticated resize to allow growing left and up
    worm_hole[2] = worm_view.winfo_width()
    worm_hole[3] = worm_view.winfo_height()

refresh_rate = int(1000/15) # 1s/fps
def on_refresh():
    img = get_worm_hole(target_win, worm_hole)
    label.configure(image=img)
    label.image = img
    label.place(x=0,y=0,width=worm_hole[2], height=worm_hole[3])

    worm_view.after(refresh_rate, on_refresh)

worm_view.after(refresh_rate, on_refresh)
worm_view.bind('<Configure>', on_config)

worm_view.mainloop()

