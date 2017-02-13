
__author__ = "Sona Bartekova, Ingrid Bohunicka, Jan Filip Kotora, Maria Meriova"
__version__ = "1.0.1"
__maintainer__ = "--"
__email__ = "--"
__status__ = "release"

# import libraries
import vlc
import sys
import cv2
from PIL import Image, ImageTk

if sys.version_info[0] < 3:
    import Tkinter as Tk
    from Tkinter import ttk
    from Tkinter.filedialog import askopenfilename, asksaveasfilename
else:
    import tkinter as Tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename, asksaveasfilename

import os
import pathlib
from threading import Thread, Event
import time
import platform
from moviepy.editor import VideoFileClip, concatenate

class Webrecording(Thread):
    """trieda ktora nahrava video"""

    def __init__(self, window, num):
        Thread.__init__(self)
        self.window = window
        self.num = num
        self.enabled = True

    def disable(self):
        self.enabled = False

    def show_frame(self):
        if not self.enabled: return
        _, frame = self.cap.read()
        frame = cv2.flip(frame, 1)
        self.out.write(frame)
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        img = img.resize((500, 400), Image.ANTIALIAS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(10, self.show_frame)

    def run(self):
        self.lmain = Tk.Label(self.window)
        self.lmain.grid(row=0, column=0)
        self.cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter('video' + self.num + '.avi', fourcc, 7.0, (640, 480))
        self.show_frame()

class RecVideo():
    """trieda ktora uchovava nahrane video"""

    def __init__(self, markcnv, displcnv, position, time, mark):
        self.markcnv = markcnv
        self.displcnv = displcnv
        self.position = position
        self.name = "video " + str(position)
        self.time = time
        self.obruc = None
        self.marked = False
        self.mark = round(mark)
        self.mark = self.markcnv.create_oval(self.mark-5, 5, self.mark+5, 15, fill="white")
        self.d1 = self.displcnv.create_text(50, (self.position * 48) - 32, text=self.name, font='arial 12')
        self.cas = round(self.time / 1000)
        self.d2 = self.displcnv.create_text(50, (self.position * 48) - 16, text=str(self.cas) + " sek.",
                                            font='arial 12')

    def rerender(self):
        """prekresli video
        -vola sa po zmene nejakeho atributu"""
        self.displcnv.delete(self.d1)
        self.displcnv.delete(self.d2)
        self.d1 = self.displcnv.create_text(50, (self.position * 48) - 32, text=self.name, font='arial 12')
        self.d2 = self.displcnv.create_text(50, (self.position * 48) - 16, text=str(self.cas) + " sek.",
                                            font='arial 12')

    def positionup(self):
        """posunie video v zozname o jedno vyssie
        -v prípade ze nejae video nad nim bolo vmazane"""
        self.position = self.position - 1
        self.name = "video " + str(self.position)
        self.obruc = None
        self.marked = False
        self.rerender()

    def mark_red(self):
        #todo premenovat
        self.marked = False
        self.markcnv.itemconfig(self.mark, fill="white")
        try: self.displcnv.delete(self.obruc)
        except:
            print("Item not found")

    def mark_blue(self):
        #todo premenovat
        self.marked = True
        self.markcnv.itemconfig(self.mark, fill="blue")
        self.obruc = self.displcnv.create_rectangle(2, self.position*48 - 48, 100, self.position*48, outline="blue", width=5)

    def bolkliknuty(self, x, y):
        """vrati True ak bolo kliknute video"""
        if 0 < x and 100 > x and (self.position * 48)-48 < y and (self.position * 48) > y:
            return True
        return False

    def ismarked(self):
        return self.marked

    def remove(self):
        """vymaze video
        - po odstraneni"""
        try:
            self.markcnv.delete(self.mark)
            self.displcnv.delete(self.d1)
            self.displcnv.delete(self.d2)
            self.displcnv.delete(self.obruc)
        except:
            print("Chyba pri odstránení")

class ttkTimer(Thread):
    #zkopirovana z netu, nieje nase vlastne riesenie
    """a class serving same function as wxTimer... but there may be better ways to do this"""

    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters

class Player(Tk.Frame):
    """hlavne okno, zpracuvava vstupy od uzivatela"""

    def __init__(self, parent, title=None):
        """constructor, vykresluje hlavný panel
        - riesi hlavne vytvaranie a umiestnovanie komponentov"""
        Tk.Frame.__init__(self, parent)
        self.camera = None
        self.parent = parent
        self.vidx = 500
        self.vidy = 400
        if title == None:
            title = "tk_vlc"
        self.parent.title(title)
        self.recnum = 0
        self.mainvidplay = False
        self.reccamplay = False
        self.recvidslist = list()

        # rolovacie menu vlavo hore
        menubar = Tk.Menu(self.parent)
        self.parent.config(menu=menubar)
        fileMenu = Tk.Menu(menubar)
        fileMenu.add_command(label="Open", underline=0, command=self.OnOpen)
        fileMenu.add_command(label="Export", underline=0, command=self.export)
        fileMenu.add_command(label="Exit", underline=1, command=_quit)
        menubar.add_cascade(label="File", menu=fileMenu)

        # panel s hlavnym prehravanim videom
        self.player = None
        self.videopanel = ttk.Frame(self.parent)
        self.mainvideopanel = ttk.Frame(self.videopanel, relief="sunken", width=self.vidx, height=self.vidy, borderwidth=5)
        self.canvas = Tk.Canvas(self.mainvideopanel, width=self.vidx, height=self.vidy).pack(side=Tk.TOP, expand=1)
        self.mainvideopanel.pack(side=Tk.TOP)
        # obsluzne talcidla hlavneho videa
        ctrlpanel = ttk.Frame(self.videopanel)
        play = ttk.Button(ctrlpanel, text="Play/Pause", command=self.OnPlay)
        stop = ttk.Button(ctrlpanel, text="Stop", command=self.OnStop)
        play.pack(side=Tk.LEFT)
        stop.pack(side=Tk.LEFT)
        # timeslider
        ctrlpanel2 = ttk.Frame(self.videopanel)
        self.scale_var = Tk.DoubleVar()
        self.timeslider_last_val = ""
        self.timeslider = Tk.Scale(ctrlpanel2, variable=self.scale_var, command=self.scale_sel,
                                   from_=0, to=1000, orient=Tk.HORIZONTAL, length=500)
        self.timeslider.pack(side=Tk.TOP, fill=Tk.X, expand=1)
        self.timeslider_last_update = time.time()
        ctrlpanel2.pack(side=Tk.TOP, fill=Tk.X)
        self.cnv = Tk.Canvas(self.videopanel, width=500, height=15, background="grey")
        self.cnv.pack(side=Tk.TOP)
        ctrlpanel.pack(side=Tk.BOTTOM)
        self.videopanel.pack(side=Tk.LEFT, expand=10)

        # panel videa nahravaneho z wbkamery
        self.recordopanel = ttk.Frame(self.parent)
        self.mainrecordpanel = ttk.Frame(self.recordopanel, relief="sunken", width=self.vidx, height=self.vidy, borderwidth=5)
        self.mainrecordpanel.pack(side=Tk.TOP)
        spacepanel = ttk.Frame(self.recordopanel, width=self.vidx, height=30)
        spacepanel.pack(side=Tk.TOP)
        # obsluzne talcidla nahravaneho videa
        ctrlpanel = ttk.Frame(self.recordopanel)
        enncamera = ttk.Button(ctrlpanel, text="camera REC/STOP", command=self.EnnCamera)
        enncamera.pack(side=Tk.LEFT)
        ctrlpanel.pack(side=Tk.BOTTOM)
        self.recordopanel.pack(side=Tk.RIGHT, expand=10)

        # canvas ktory zobrazuje zoznam nahranyh videi
        self.cnvrec = Tk.Canvas(self.parent, width=100, height=self.vidy)
        self.cnvrec.create_rectangle(2, 2, 100, self.vidy, outline="grey")
        self.cnvrec.create_rectangle(2, self.vidy-30, 100, self.vidy, outline="black")
        self.cnvrec.create_text(50, self.vidy-15, text="VYMAŽ", font='arial 10')
        self.cnvrec.pack(side=Tk.RIGHT)
        self.cnvrec.bind('<Button-1>', self.rec_klik)

        # VLC player controls
        # z triedy ktoru sme zobrali z netu na prehravanie videa
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()
        self.timer = ttkTimer(self.OnTimer, 1.0)
        self.timer.start()
        self.parent.update()

        # ----- funkcie ktore implementuju chovanaie jednotlivych tlacidiel -----
    def OnExit(self, evt):
        """zatvori okno"""
        self.Close()

    def OnOpen(self):
        """otvori filedialog, a po vybere videa ho nacita do hlavneho okna"""
        # ak bezi vide najprv ho zavrie
        self.OnStop()

        # otvori novy filedialog
        # p uchovava cestu kde sa otvori filedialog (home v tomto pripade)
        p = pathlib.Path(os.path.expanduser("~"))
        fullname = askopenfilename(initialdir=p, title="choose your file",
                                   filetypes=(("all files", "*.*"), ("mp4 files", "*.mp4")))
        if os.path.isfile(fullname):
            self.fullpath = fullname
            dirname = os.path.dirname(fullname)
            self.filename = os.path.basename(fullname)
            self.Media = self.Instance.media_new(str(os.path.join(dirname, self.filename)))
            self.player.set_media(self.Media)
            self.player.set_hwnd(self.GetHandle())
            self.OnPlay()

    def OnPlay(self):
        """meni status Play/Pause.
        ak nieje otvorene ziadne video, otvori filedialog"""
        if self.reccamplay is True: return
        if not self.player.get_media():
            self.OnOpen()
        else:
            if self.mainvidplay == False:
                self.mainvidplay = True
                if self.player.play() == -1:
                    self.mainvidplay = False
                    self.errorDialog("Unable to play.")
            else:
                self.player.pause()
                self.mainvidplay = False

    def GetHandle(self):
        return self.mainvideopanel.winfo_id()

    def OnStop(self):
        """zastavy prehravac"""
        self.player.stop()
        # reset the time slider
        self.timeslider.set(0)
        self.mainvidplay = False

    def OnTimer(self):
        """zavola sa po zmene timeru uzivatelom, nastavi videu novy cas"""
        if self.player == None:
            return
        length = self.player.get_length()
        dbl = length * 0.001
        self.timeslider.config(to=dbl)
        tyme = self.player.get_time()
        if tyme == -1:
            tyme = 0
        dbl = tyme * 0.001
        self.timeslider_last_val = ("%.0f" % dbl) + ".0"
        if time.time() > (self.timeslider_last_update + 2.0):
            self.timeslider.set(dbl)

    def scale_sel(self, evt):
        if self.player == None:
            return
        nval = self.scale_var.get()
        sval = str(nval)
        if self.timeslider_last_val != sval:
            self.timeslider_last_update = time.time()
            mval = "%.0f" % (nval * 1000)
            self.player.set_time(int(mval))  # milliseconds

    def EnnCamera(self):
        """"zapne/vpne webkameru"""
        if self.mainvidplay == True: return
        if self.reccamplay == False:
            self.reccamplay = True
            self.recnum += 1
            self.camera = Webrecording(self.mainrecordpanel, str(self.recnum))
            self.camera.start()
            position = self.player.get_time() / (self.player.get_length() / 500)
            self.recvidslist.append(RecVideo(self.cnv, self.cnvrec, self.recnum, self.player.get_time(), position))
        else:
            self.camera.disable()
            self.reccamplay = False

    def rec_klik(self, event):
        """kontroluje ci nebolo oznacene niektore z natocenych videii
        - v pripade ze ano, oznaci dane video"""
        if self.bolvymazklik(event.x, event.y):
            for i in self.recvidslist:
                if i.ismarked():
                    tmp = i
                    break
            tmp.remove()
            self.recvidslist.remove(tmp)
            tmp = tmp.position
            for i in self.recvidslist:
                if i.position > tmp:
                    i.positionup()
            self.recnum = self.recnum - 1
            return
        kliknute = None
        for i in self.recvidslist:
            if i.bolkliknuty(event.x, event.y) is True:
                kliknute = i
                break
        for i in self.recvidslist:
            i.mark_red()
        kliknute.mark_blue()

    def bolvymazklik(self, x, y):
        """kontroluje ci nebolo kliknuty button vymaz"""
        if 0 < x and 100 > x and self.vidy-30 < y and self.vidy > y:
            return True
        return False

    def export(self):
        """"export final video"""
        results = []
        # split, rozdeli hlavne video tak aby donho mohli byt vlozene dotocene casti
        a = 0
        # raw.mp4 je pomocne video ktore sa vytvara pre potrebu
        # konvertovat hlavne video do formatu .mp4
        try:
            os.remove("raw.mp4")
        except OSError:
            pass
        os.system("kk\\ffmpeg -i " + self.fullpath + " -s 640x480 raw.mp4")
        # samotne delenie videa
        for i in self.recvidslist:
            kk = VideoFileClip("raw.mp4")
            k = kk.subclip(a, i.cas)
            results.append(k)
            a = i.cas
            j = str(i.position)
            try:
                os.remove("video" + j + ".mp4")
            except OSError:
                pass
            os.system("kk\\ffmpeg -i video" + j + ".avi video" + j + ".mp4")
            results.append(VideoFileClip("video" + j + ".mp4"))

        b = round(self.player.get_length()/1000)
        results.append(VideoFileClip("raw.mp4").subclip(a, b))
        # merge, spojenie videi dokopy, videa su ulozene v poli 'results'
        res = concatenate(results)
        #save as, otvori filedialog a ulozi video na zadanu adresu
        p = os.path.dirname(self.fullpath)
        f = asksaveasfilename(initialdir=p, title="save your file")
        res.write_videofile(f + '.mp4', fps=15, codec='mpeg4', audio=False)

    def errorDialog(self, errormessage):
        """Display a simple error dialog."""
        """toto asi ani nepouzivame"""
        edialog = Tk.tkMessageBox.showerror(self, 'Error', errormessage)

def Tk_get_root():
    if not hasattr(Tk_get_root, "root"):
        Tk_get_root.root = Tk.Tk()
    return Tk_get_root.root

def _quit():
    print("_quit: bye")
    root = Tk_get_root()
    root.quit()
    root.destroy()
    os._exit(1)

if __name__ == "__main__":
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)

    player = Player(root, title="tkinter vlc")
    root.mainloop()
