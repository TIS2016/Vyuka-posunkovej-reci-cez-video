## dokumentacia
## https://www.olivieraubert.net/vlc/python-ctypes/doc/

import vlc
import sys
import cv2
from PIL import Image, ImageTk


if sys.version_info[0] < 3:
    import Tkinter as Tk
    from Tkinter import ttk
    from Tkinter.filedialog import askopenfilename
else:
    import tkinter as Tk
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename

# import standard libraries
import os
import pathlib
from threading import Timer, Thread, Event
import time
import platform

class webrecording(Thread):

    def __init__(self, window):
        Thread.__init__(self)
        self.window = window
        self.enabled = True

    def disable(self):
        self.enabled = False

    def terminate(self):
        pass

    def show_frame(self):
        if not self.enabled: return
        _, frame = self.cap.read()
        frame = cv2.flip(frame, 1)
        # print(frame)
        self.out.write(frame)
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(10, self.show_frame)

    def run(self):
        # Graphics window
        #imageFrame = tk.Frame(window, width=600, height=500)
        #imageFrame.grid(row=0, column=0, padx=10, pady=2)

        # Capture video frames
        self.lmain = Tk.Label(self.window)
        self.lmain.grid(row=0, column=0)
        self.cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter('video.avi', fourcc, 7.0, (640, 480))

        # Slider window (slider controls stage position)

        sliderFrame = Tk.Frame(self.window, width=600, height=100)
        sliderFrame.grid(row=600, column=0, padx=10, pady=2)

        self.show_frame()  # Display 2
        # window.protocol("WM_DELETE_WINDOW", out.release())
        # Starts GUI
        # OSETRIT ukoncenie nahravania a aj vypnutie kamery

class ttkTimer(Thread):
    """a class serving same function as wxTimer... but there may be better ways to do this
    """

    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        # print("callback= ", callback())
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()
            # print("ttkTimer start")

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters


# def doit():
#    print("hey dude")

# code to demo ttkTimer
# t = ttkTimer(doit, 1.0)
# t.start()
# time.sleep(5)
# print("t.get= ", t.get())
# t.stop()
# print("timer should be stopped now")


class Player(Tk.Frame):
    """The main window has to deal with events.
    """

    def __init__(self, parent, title=None):
        Tk.Frame.__init__(self, parent)

        self.camera = None
        self.parent = parent
        self.vidx = 400
        self.vidy = 300

        if title == None:
            title = "tk_vlc"
        self.parent.title(title)

        # Menu Bar
        #   File Menu
        menubar = Tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        fileMenu = Tk.Menu(menubar)
        fileMenu.add_command(label="Open", underline=0, command=self.OnOpen)
        fileMenu.add_command(label="Exit", underline=1, command=_quit)
        menubar.add_cascade(label="File", menu=fileMenu)

        # The second panel holds controls
        self.player = None
        self.videopanel = ttk.Frame(self.parent, borderwidth=5, relief="sunken", width=self.vidx, height=self.vidy)
        self.canvas = Tk.Canvas(self.videopanel, width=self.vidx, height=self.vidy).pack(side=Tk.TOP, expand=1)
        self.videopanel.pack(side=Tk.LEFT, expand=10)

        # recordpanel holds video from web-cam
        self.recordopanel = ttk.Frame(self.parent, borderwidth=5, relief="sunken", width=self.vidx, height=self.vidy)
        self.recordopanel.pack(side=Tk.RIGHT, expand=10)

        camerapanel = ttk.Frame(self.parent)
        enncamera = ttk.Button(camerapanel, text="camera ON", command=self.EnnCamera)
        discamera = ttk.Button(camerapanel, text="camera OFF", command=self.DisCamera)
        enncamera.pack(side=Tk.LEFT)
        discamera.pack(side=Tk.LEFT)
        camerapanel.pack(side=Tk.TOP)

        ctrlpanel = ttk.Frame(self.parent)
        pause = ttk.Button(ctrlpanel, text="Pause", command=self.OnPause)
        play = ttk.Button(ctrlpanel, text="Play", command=self.OnPlay)
        stop = ttk.Button(ctrlpanel, text="Stop", command=self.OnStop)
        volume = ttk.Button(ctrlpanel, text="Volume", command=self.OnSetVolume)
        pause.pack(side=Tk.LEFT)
        play.pack(side=Tk.LEFT)
        stop.pack(side=Tk.LEFT)
        volume.pack(side=Tk.LEFT)
        self.volume_var = Tk.IntVar()
        self.volslider = Tk.Scale(ctrlpanel, variable=self.volume_var, command=self.volume_sel,
                                  from_=0, to=100, orient=Tk.HORIZONTAL, length=100)
        self.volslider.pack(side=Tk.LEFT)
        ctrlpanel.pack(side=Tk.BOTTOM)

        ctrlpanel2 = ttk.Frame(self.parent)
        self.scale_var = Tk.DoubleVar()
        self.timeslider_last_val = ""
        self.timeslider = Tk.Scale(ctrlpanel2, variable=self.scale_var, command=self.scale_sel,
                                   from_=0, to=1000, orient=Tk.HORIZONTAL, length=500)
        self.timeslider.pack(side=Tk.BOTTOM, fill=Tk.X, expand=1)
        self.timeslider_last_update = time.time()
        ctrlpanel2.pack(side=Tk.BOTTOM, fill=Tk.X)

        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()

        # below is a test, now use the File->Open file menu
        # media = self.Instance.media_new('output.mp4')
        # self.player.set_media(media)
        # self.player.play() # hit the player button
        # self.player.video_set_deinterlace(str_to_bytes('yadif'))

        self.timer = ttkTimer(self.OnTimer, 1.0)
        self.timer.start()
        self.parent.update()

        # self.player.set_hwnd(self.GetHandle()) # for windows, OnOpen does does this

    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()

    def OnOpen(self):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # if a file is already running, then stop it.
        self.OnStop()

        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        p = pathlib.Path(os.path.expanduser("~"))
        fullname = askopenfilename(initialdir=p, title="choose your file",
                                   filetypes=(("all files", "*.*"), ("mp4 files", "*.mp4")))
        if os.path.isfile(fullname):
            print(fullname)
            splt = os.path.split(fullname)
            dirname = os.path.dirname(fullname)
            filename = os.path.basename(fullname)
            # Creation
            self.Media = self.Instance.media_new(str(os.path.join(dirname, filename)))
            self.player.set_media(self.Media)
            # Report the title of the file chosen
            # title = self.player.get_title()
            #  if an error was encountred while retriving the title, then use
            #  filename
            # if title == -1:
            #    title = filename
            # self.SetTitle("%s - tkVLCplayer" % title)

            # set the window id where to render VLC's video output
            if platform.system() == 'Windows':
                self.player.set_hwnd(self.GetHandle())
            else:
                self.player.set_xwindow(self.GetHandle())  # this line messes up windows
            # FIXME: this should be made cross-platform
            self.OnPlay()

            # set the volume slider to the current volume
            # self.volslider.SetValue(self.player.audio_get_volume() / 2)
            self.volslider.set(self.player.audio_get_volume())

    def OnPlay(self):
        """Toggle the status to Play/Pause.
        If no file is loaded, open the dialog window.
        """
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        if not self.player.get_media():
            self.OnOpen()
        else:
            # Try to launch the media, if this fails display an error message
            if self.player.play() == -1:
                self.errorDialog("Unable to play.")

    def GetHandle(self):
        return self.videopanel.winfo_id()

    # def OnPause(self, evt):
    def OnPause(self):
        """Pause the player.
        """
        self.player.pause()

    def OnStop(self):
        """Stop the player.
        """
        self.player.stop()
        # reset the time slider
        self.timeslider.set(0)

    def OnTimer(self):
        """Update the time slider according to the current movie time.
        """
        if self.player == None:
            return
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        length = self.player.get_length()
        dbl = length * 0.001
        self.timeslider.config(to=dbl)

        # update the time on the slider
        tyme = self.player.get_time()
        if tyme == -1:
            tyme = 0
        dbl = tyme * 0.001
        self.timeslider_last_val = ("%.0f" % dbl) + ".0"
        # don't want to programatically change slider while user is messing with it.
        # wait 2 seconds after user lets go of slider
        if time.time() > (self.timeslider_last_update + 2.0):
            self.timeslider.set(dbl)

    def scale_sel(self, evt):
        if self.player == None:
            return
        nval = self.scale_var.get()
        sval = str(nval)
        if self.timeslider_last_val != sval:
            # this is a hack. The timer updates the time slider.
            # This change causes this rtn (the 'slider has changed' rtn) to be invoked.
            # I can't tell the difference between when the user has manually moved the slider and when
            # the timer changed the slider. But when the user moves the slider tkinter only notifies
            # this rtn about once per second and when the slider has quit moving.
            # Also, the tkinter notification value has no fractional seconds.
            # The timer update rtn saves off the last update value (rounded to integer seconds) in timeslider_last_val
            # if the notification time (sval) is the same as the last saved time timeslider_last_val then
            # we know that this notification is due to the timer changing the slider.
            # otherwise the notification is due to the user changing the slider.
            # if the user is changing the slider then I have the timer routine wait for at least
            # 2 seconds before it starts updating the slider again (so the timer doesn't start fighting with the
            # user)
            # selection = "Value, last = " + sval + " " + str(self.timeslider_last_val)
            # print("selection= ", selection)
            self.timeslider_last_update = time.time()
            mval = "%.0f" % (nval * 1000)
            self.player.set_time(int(mval))  # expects milliseconds
            print(self.player.get_time())

    def EnnCamera(self):
        """"zapne webkameru"""
        print("kamera zapnuta")
        self.camera = webrecording(self.recordopanel)
        self.camera.start()

    def DisCamera(self):
        """vypne webkameru"""
        print("kamera vypnuta")
        # todo
        # problem z komunikaciou z threadom
        self.camera.disable()
        #self.camera.kill()

    def volume_sel(self, evt):
        if self.player == None:
            return
        volume = self.volume_var.get()
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def OnToggleVolume(self, evt):
        """Mute/Unmute according to the audio button.
        """
        is_mute = self.player.audio_get_mute()

        self.player.audio_set_mute(not is_mute)
        # update the volume slider;
        # since vlc volume range is in [0, 200],
        # and our volume slider has range [0, 100], just divide by 2.
        self.volume_var.set(self.player.audio_get_volume())

    def OnSetVolume(self):
        """Set the volume according to the volume sider.
        """
        volume = self.volume_var.get()
        print("volume= ", volume)
        # volume = self.volslider.get() * 2
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if volume > 100:
            volume = 100
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

    def errorDialog(self, errormessage):
        """Display a simple error dialog.
        """
        edialog = Tk.tkMessageBox.showerror(self, 'Error', errormessage)


def Tk_get_root():
    if not hasattr(Tk_get_root, "root"):  # (1)
        Tk_get_root.root = Tk.Tk()  # initialization call is inside the function
    return Tk_get_root.root


def _quit():
    print("_quit: bye")
    root = Tk_get_root()
    root.quit()  # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    os._exit(1)


if __name__ == "__main__":
    # Create a Tk.App(), which handles the windowing system event loop
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)

    player = Player(root, title="tkinter vlc")
    # show the player window centred and run the application
    root.mainloop()
