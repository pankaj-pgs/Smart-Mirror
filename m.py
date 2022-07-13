# smartmirror.py
# requirements
# requests, feedparser, traceback, Pillow

from threading import Thread
from time import sleep
import pyttsx3
import datetime
from speech_recognition import Microphone, Recognizer, AudioFile, UnknownValueError
from gtts import gTTS 
import os

from tkinter import *
import locale
import threading
import time
import requests
import json
import traceback
import feedparser
import webbrowser

from PIL import Image, ImageTk
from contextlib import contextmanager

from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

LOCALE_LOCK = threading.Lock()

ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 24 # 12 or 24
date_format = "%b %d, %Y" # check python doc for strftime() for options
news_country_code = 'india'
weather_api_token = '<TOKEN>' # create account at https://darksky.net/dev/
weather_lang = 'en' # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us' # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
latitude = None # Set this if IP location lookup does not work for you (must be a string)
longitude = None # Set this if IP location lookup does not work for you (must be a string)
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18

@contextmanager
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
    'clear-day': "assets/Sun.png",  # clear sky day
    'wind': "assets/Wind.png",   #wind
    'cloudy': "assets/Cloud.png",  # cloudy day
    'partly-cloudy-day': "assets/PartlySunny.png",  # partly cloudy day
    'rain': "assets/Rain.png",  # rain day
    'snow': "assets/Snow.png",  # snow day
    'snow-thin': "assets/Snow.png",  # sleet day
    'fog': "assets/Haze.png",  # fog day
    'clear-night': "assets/Moon.png",  # clear sky night
    'partly-cloudy-night': "assets/PartlyMoon.png",  # scattered clouds night
    'thunderstorm': "assets/Storm.png",  # thunderstorm
    'tornado': "assests/Tornado.png",    # tornado
    'hail': "assests/Hail.png"  # hail
}


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Times', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Times', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Times', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #hour in 12h format
            else:
                time2 = time.strftime('%H:%M') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)





class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News' # 'News' is more internationally generic
        self.newsLbl = Label(self, text=self.title, font=('Times', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP)
        self.get_headlines()
        self.image = Image. open('assets/mic.png')
        # The (450, 350) is (height, width)
        self.image = self.image.resize((50,50), Image. ANTIALIAS)
        self.my_img = ImageTk. PhotoImage(self.image)
        '''def lis():  
            recog = Recognizer()
            mic = Microphone()

            with mic:
                print("Talk")
                audio = recog.record(mic, 4)

            try:
                recognized = recog.recognize_google(audio)
                print("you said: ",recognized)

            except UnknownValueError:
                print("Unable to recognize")
                speak("please retry")
            if recognized == "hello" or recognized == "hai" :
                speak("how are you")
            elif recognized=="what's a time" or recognized=="what's the time" or recognized=="whats a time" or recognized=="whats the time":
                l() 

            elif recognized == "no thanks":
                speak("ok")
            elif recognized == "open YouTube":
                speak("ok")
                webbrowser.open('https://www.youtube.com/')
            elif recognized == "open Instagram":
                speak("ok")
                webbrowser.open('https://www.instagram.com/')
            elif recognized == "open Facebook":
                speak("ok")
                webbrowser.open('https://www.facebook.com/')
            elif recognized == "open Twitter":
                speak("ok")
                webbrowser.open('https://www.twitter.com/')
                
            else:
                answer = bot.get_response(recognized)
                speak(answer)'''
        self.mi = Button(self,image=self.my_img,command=lis,state=NORMAL).pack(side=BOTTOM,anchor=SE)

    def get_headlines(self):
        try:
            # remove all children
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
            if news_country_code == None:
                headlines_url = "https://news.google.com/news?ned=us&output=rss"
            else:
                headlines_url = "https://news.google.com/news?ned=%s&output=rss" % news_country_code

            feed = feedparser.parse(headlines_url)

            for post in feed.entries[0:5]:
                headline = NewsHeadline(self.headlinesContainer, post.title)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            #print "Error: %s. Cannot get news." % e

        self.after(600000, self.get_headlines)


class NewsHeadline(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')

        image = Image.open("assets/Newspaper.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)


        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Times', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=LEFT, anchor=N)


class Calendar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'Calendar Events'
        self.calendarLbl = Label(self, text=self.title, font=('Times', medium_text_size), fg="white", bg="black")
        self.calendarLbl.pack(side=TOP, anchor=E)
        self.calendarEventContainer = Frame(self, bg='black')
        self.calendarEventContainer.pack(side=TOP, anchor=E)
        self.get_events()

    def get_events(self):
        #TODO: implement this method
        # reference https://developers.google.com/google-apps/calendar/quickstart/python

        # remove all children
        for widget in self.calendarEventContainer.winfo_children():
            widget.destroy()

        calendar_event = CalendarEvent(self.calendarEventContainer)
        calendar_event.pack(side=TOP, anchor=E)
        pass


class CalendarEvent(Frame):
    def __init__(self, parent, event_name="Event 1"):
        Frame.__init__(self, parent, bg='black')
        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=TOP, anchor=E)

class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        api_address='http://api.openweathermap.org/data/2.5/weather?appid=0053e9bbb2858993046d610bd0b72d89&q=chinchwad'
        json_data = requests.get(api_address).json()
        format_add = json_data['main']
        temp1 = int(float(format_add["temp"])-273.15)
        w = json_data['weather']
        wt = w[0]
        weather = wt["main"]
        dec = wt["description"]
        print(weather)
        print(temp1)

        temp = str(temp1)+"°C"
        if weather == "Cloud":
            self.image = Image. open('assets/Cloud.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            #print(temp)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather == "Rain":
            self.image = Image. open('assets/Rain.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            #print(temp)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Moon":
            self.image = Image. open('assets/Moon.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
            #print(temp)
        elif weather =="Sun":
            self.image = Image. open('assets/Sun.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Hail":
            self.image = Image. open('assets/Hail.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Wind":
            self.image = Image. open('assets/Wind.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Sunrise":
            self.image = Image. open('assets/Sunrise.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="PartlyMoon":
            self.image = Image. open('assets/PartlyMoon.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="PartlySunny":
            self.image = Image. open('assets/PartlySunny.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Snow":
            self.image = Image. open('assets/Snow.png')
            # The (450, d350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Storm":
            self.image = Image. open('assets/Storm.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Tornado":
            self.image = Image. open('assets/Tornado.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Haze":
            self.image = Image. open('assets/Haze.png')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")
        elif weather =="Clear":
            self.image = Image. open('assets/Clear.jpg')
            # The (450, 350) is (height, width)
            self.image = self.image.resize((50,50), Image. ANTIALIAS)
            self.my_img = ImageTk. PhotoImage(self.image)
            self.t = Label(self, image=self.my_img,justify=LEFT,padx = 0, pady = 0).pack(side="left")

        self.tl = Label(self,text="Chinchwad, Pune \n"+weather+",\n"+dec,bg="black",width=15,fg="white",font=("Times", 10)).pack(side=LEFT, anchor=NW)
        self.tl = Label(self,text=temp,bg="black",width=4,fg="white",font=("Helvetica", 44)).pack(side=LEFT, anchor=NW)
       

class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
        # weather
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        # news
        self.news = News(self.bottomFrame)
        self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)

        
        # calender - removing for now
        self.calender = Calendar(self.bottomFrame)
        self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"


    #w = FullscreenWindow()
    #w.tk.mainloop()
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
print(voices[1].id)
engine.setProperty('voice', voices[1].id)
engine. setProperty("rate", 150)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()
    pass
def l():
    hour = str(datetime.datetime.now().hour)
    minuites = str(datetime.datetime.now().minute)
    sec = str(datetime.datetime.now().second)
    time = hour+"hour"+minuites+"minuites"+sec+"seconds"
    speak(time)

    pass
def wishMe():
    hour = int(datetime.datetime.now().hour)
    if hour>=0 and hour<12:
        speak("Good Morning!")
    
    elif hour>=12 and hour<18:
        speak("Good Afternoon!")

    else:
        speak("Good Evening!")

    pass


def lis():  
    recog = Recognizer()
    mic = Microphone()

    with mic:
        print("Talk")
        audio = recog.record(mic, 4)

    try:
        recognized = recog.recognize_google(audio)
        print("you said: ",recognized)

    except UnknownValueError:
        print("Unable to recognize")
        speak("please retry")
    if recognized == "hello" or recognized == "hai" :
        speak("how are you")
    elif recognized=="what's a time" or recognized=="what's the time" or recognized=="whats a time" or recognized=="whats the time":
        l() 

    elif recognized == "no thanks":
        speak("ok")
    elif recognized == "open YouTube":
        speak("ok")
        webbrowser.open('https://www.youtube.com/')
    elif recognized == "open Instagram":
        speak("ok")
        webbrowser.open('https://www.instagram.com/')
    elif recognized == "open Facebook":
        speak("ok")
        webbrowser.open('https://www.facebook.com/')
    elif recognized == "open Twitter":
        speak("ok")
        webbrowser.open('https://www.twitter.com/')
        
    else:
        answer = bot.get_response(recognized)
        speak(answer)


bot = ChatBot("My Bot")

convo = [
    'hello',
    'hi there !',
    'What’s your name?',
    'I am your Personal AI',

    'Where are you from?',
    'I’m in your device',

    'What is your surname?',
    'I dont have Surname',

    'good morning?',
    'Good morning to you too',

    'how do you do?',
    'how are you?',
    'i am cool.'
    'fine, you?',
    'always cool.',
    'i am ok',
    'glad to hear that.',
    'i am fine',
    'glad to hear that.',
    'i feel awesome'
    'excellent, glad to hear that.',
    'not so good',
    'sorry to hear that.',
    
    'how are you doing?',
    'I am doing very well thank you for asking',
    
    'thank you?',
    'my pleasure'


    
]

trainer = ListTrainer(bot)

# now training the bot with the help of trainer

trainer.train(convo)
w = FullscreenWindow()
ws = w.tk.winfo_screenwidth()
h = w.tk.winfo_screenheight()
w.tk.geometry("%dx%d+0+0" % (ws, h))
photo = PhotoImage(file = "assets/logo.png")
w.tk.iconphoto(False, photo)
w.tk.title("SMART MIRROR")
w.tk.overrideredirect(1)
w.tk.mainloop()
