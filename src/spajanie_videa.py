from moviepy.editor import *
a = VideoFileClip('video1.avi')
b = VideoFileClip('video2.avi')
#b = VideoFileClip('video2.avi')
#c = VideoFileClip('video3.avi')


video = concatenate([a,b])
#video = CompositeVideoClip([a.set_pos((45,150)),b.set_pos((90,100))], size=(720,460))

video.write_videofile("result.mp4",fps=15, codec='mpeg4', audio=False) #funguje s .mp4 videami
#video.write_videofile("result.avi",fps=15, codec='png', audio=False)  hadze chybu

