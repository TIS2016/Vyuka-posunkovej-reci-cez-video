from moviepy.editor import VideoFileClip
import tkinter as tk
from PIL import Image, ImageTk


def frame_to_image(arr):
    mode = 'RGB'
    height, width, channels = arr.shape
    arr = arr.reshape(width * channels, height)
    return Image.frombuffer(mode, (width, height), arr.tostring(), 'raw', mode, 0, 1)


window = tk.Tk()
canvas = tk.Canvas(window, width=1280, height=720)
canvas.pack()


video = VideoFileClip('aa.mp4')
num_frame = 20
frame = video.get_frame(num_frame)
image = ImageTk.PhotoImage(frame_to_image(frame))
image_id = canvas.create_image(400, 400, image=image)
window.mainloop()
