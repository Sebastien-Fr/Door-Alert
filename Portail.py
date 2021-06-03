import smtplib,ssl  
from picamera import PiCamera  
from time import sleep  
from email.mime.multipart import MIMEMultipart  
from email.mime.base import MIMEBase  
from email.mime.text import MIMEText  
from email.utils import formatdate  
from email import encoders
import RPi.GPIO as GPIO
import logging
from logging.handlers import RotatingFileHandler
import time
import datetime
from datetime import timedelta
from datetime import date
from datetime import datetime
import threading, os, signal
import subprocess
from subprocess import check_call, call
import io
import socket
import struct
import ctypes
import socketserver
from threading import Condition
import tkinter
from tkinter import *
from tkinter import ttk
import threading
mainWin = Tk()
mainWin.title('CAM')
test=0
bt=0
buffer = io.BytesIO()

#*******************logger**********************
logger = logging.getLogger('portail')
logger.setLevel(logging.DEBUG)
fh= RotatingFileHandler('portail.log',maxBytes=1000000, backupCount=5)
#fh = logging.FileHandler('portail.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)

#*******************gpio**********************
GPIO.setmode(GPIO.BOARD)
#ignore les msg d'alarme 
GPIO.setwarnings(False)
#affectation des pin gpio Custard pi 2
#entree

GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#sorties 
GPIO.setup(11, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
camera = PiCamera()

###################################################################
def Record():
      class StreamingOutput(object):#raz buffer a chaque nouvelle frame
          def __init__(self):
              self.frame = None
              self.buffer = io.BytesIO()
              self.condition = Condition()

          def write(self, buf):
              if buf.startswith(b'\xff\xd8'):
                  self.buffer.truncate()
                  with self.condition:
                      self.frame = self.buffer.getvalue()
                      self.condition.notify_all()
                  self.buffer.seek(0)
              return self.buffer.write(buf)          
      print ('record')
      global output
      output=StreamingOutput()      
      camera.resolution = (1024, 768)
      camera.framerate=24
      camera.start_recording(output, format='mjpeg')
            
def TakePics():
    
    camera.stop_recording()
    time.sleep(0.5)
    print('capture en cours')
    camera.resolution = (1024, 768)
    camera.start_preview()  
    sleep(0.1)  
    camera.capture('/home/pi/image.jpg')
    sleep(1.5)
    camera.capture('/home/pi/image2.jpg')
    sleep(2)
    camera.capture('/home/pi/image3.jpg')
    camera.stop_preview()
    #print ('fin capture, encodage')
    logger.info('end capture')
    send_an_email()
   
def send_an_email():
    Timestamp=datetime.now()
    Timestampformat=Timestamp.strftime("%d/%m/%Y %H:%M:%S")
    destinataires=['XXXXXX@gmail.com','XXXXXX@XXXXX.fr' ]
    me = 'XXXXXXXXX@gmail.com'
    subject = "Portail Ouvert " + Timestampformat   
  
    msg = MIMEMultipart()  
    msg['Subject'] = subject  
    msg['From'] = me  
    msg['To'] =  ', '.join(destinataires)
    msg.preamble = "Portail "
    
    files = [
    'image.jpg',
    'image2.jpg',
    'image3.jpg']
#***********************encode files**************    
    for file in files:
        #print('encode = ' + file)
        logger.info('encode = ' + file)
        part = MIMEBase('application', "octet-stream")  
        part.set_payload(open('/home/pi/'+file, "rb").read())  
        encoders.encode_base64(part)  
        part.add_header('Content-Disposition', 'attachment; filename=image.jpg')
        msg.attach(part)  
#*******************send mail*********************
    try:
       #print('sending')
       s = smtplib.SMTP('smtp.gmail.com', 587)  
       s.ehlo()  
       s.starttls()  
       s.ehlo()  
       s.login(user = 'XXXXXXXX@gmail.com', password = 'XXXXXXX')
       s.sendmail(me, destinataires, msg.as_string())  
       s.quit()
       logger.info('mail sent')       
    except:  
          #print ("Error: unable to send email --resend")
          logger.info('Error: unable to send email')
          time.sleep(5)
          send_an_email()
        
def sendminimail(subject):
    Timestamp=datetime.now()
    Timestampformat=Timestamp.strftime("%d/%m/%Y %H:%M:%S")
    destinataires=['XXXXXXXX@gmail.com','XXXXXXX@XXXX.fr']
    me = 'XXXXXXXX@gmail.com'
    subject = subject+ Timestampformat 
    msg = MIMEMultipart()  
    msg['Subject'] = subject  
    msg['From'] = me  
    msg['To'] = ', '.join(destinataires)
    msg.preamble = "test "
    try:
       s = smtplib.SMTP('smtp.gmail.com', 587)
       s.ehlo()  
       s.starttls()  
       s.ehlo()  
       s.login(user = 'XXXXXXXX@gmail.com', password = 'XXXXXXX')   
       s.sendmail(me, destinataires, msg.as_string())  
       s.quit()
       logger.info('sent test email')
    except:  
          # print ("Error: unable to send email --resend")
          logger.info('Error: unable to send test email')

#***************stream********web server*******************

class streamF(threading.Thread):
     def __init__(self,nom = 'stream', *args, **kwargs):
      threading.Thread.__init__(self)
      super(streamF, self).__init__(*args, **kwargs)
      self._stop_event = threading.Event()
      self.nom=nom
      self.terminated = False
      self.test=0
     def run(self): 
            print ('stream')
            from http import server
            logger.info('start streaming')
            PAGE="""\
            <html>
            <head>
            <title>Raspberry Pi - Surveillance Camera</title>
            </head>
            <body>
            <center><h1>Raspberry Pi - Surveillance Camera</h1></center>
            <center><img src="stream.mjpg" width="640" height="480"></center>
            </body>
            </html>
            """
            class StreamingHandler(server.BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/':
                        self.send_response(301)
                        self.send_header('Location', '/index.html')
                        self.end_headers()
                    elif self.path == '/index.html':
                        content = PAGE.encode('utf-8')
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html')
                        self.send_header('Content-Length', len(content))
                        self.end_headers()
                        self.wfile.write(content) 
                    elif self.path == '/stream.mjpg':
                        self.send_response(200)
                        self.send_header('Age', 0)
                        self.send_header('Cache-Control', 'no-cache, private')
                        self.send_header('Pragma', 'no-cache')
                        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
                        self.end_headers()
                        try:
                            while True:
                                frame = output.frame
                                self.wfile.write(b'--FRAME\r\n')
                                self.send_header('Content-Type', 'image/jpeg')
                                self.send_header('Content-Length', len(frame))
                                self.end_headers()
                                self.wfile.write(frame)
                                self.wfile.write(b'\r\n')
                        except Exception as e:
                            logger.info(
                                'Removed streaming client %s: %s',
                                self.client_address, str(e))
                            print (
                                'Removed streaming client %s: %s',
                                self.client_address, str(e))
                    else:
                        self.send_error(404)
                        self.end_headers()
            class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
                allow_reuse_address = True
                daemon_threads = True
            try:
                address = ('192.168.0.XXX', 8000)
                server = StreamingServer(address, StreamingHandler)
                server.serve_forever()
            finally:
                print('stop server')
                                  
######################  wait for edge  ###########################################
class Waitgpio(threading.Thread):
     def __init__(self,nom = 'Waitgpio'):
      threading.Thread.__init__(self)
      self.nom=nom
      self.terminated = False
      self.test=0
     def run(self):
            memo=0
            init=1
            print ('wait gpio')
            #****************button************************************
            def ButtonTest():
                global bt
                bt=1             
            #Tk    
            B1= ttk.Button(text='shot',command =  ButtonTest)
            B1.grid(row=1,column=1)
            L1=ttk.Label(mainWin,width=13,text='init')
            L1.grid(row=1,column =2)
            while True:
                global bt
                mainWin.update()
                #attend info portail contact NC
                if  (GPIO.input(22)and memo) :
                    memo=0
                    logger.info('gpio off')
                    #print('gpio off')
                    Record()  
                    L1.configure(text='streaming')
                    
                if (not GPIO.input(22)and not memo)or bt==1 :
                    memo=1
                    bt=0
                    logger.info('gpio on')
                    #print('gpio on')
                    L1.configure(text='shotting')
                    TakePics()
                    
                if init :
                    init=0
                    logger.info('init')
                    sendminimail('init  ')
                    memo=1
                    
     def stop(self):
                 self._stopevent.set()
#######################################################################
                           
edge=Waitgpio()
edge.start()
flux=streamF()
flux.start()
mainWin.mainloop() 


       
