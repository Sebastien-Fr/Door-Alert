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
import io
import socket
import struct



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
#*************init****************************
camera = PiCamera()
memo=0
init=1
    
def TakePics():
    
    #print('capture en cours')
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
    destinataires=['XXXXXX@gmail.com']
    me = 'XXXXXX@gmail.com'
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
        part.set_payload(open(file, "rb").read())  
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
       s.login(user = 'XXXXXXX@gmail.com', password = 'XXXXXXXXX')
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
    destinataires=['XXXXXX@gmail.com']
    me = 'XXXXXX@gmail.com'
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
       s.login(user = 'XXXXXX@gmail.com', password = 'XXXXXXXXX')   
       s.sendmail(me, destinataires, msg.as_string())  
       s.quit()
       logger.info('sent test email')
    except:  
          # print ("Error: unable to send email --resend")
          logger.info('Error: unable to send test email')


#***************wait for edge******************************
while True:
    
    #attend info portail contact NC
    if  GPIO.input(22) and  memo:
        memo=0
        
        logger.info('gpio off')

    if not  GPIO.input(22)and not memo:
        memo=1
        logger.info('gpio on')
        TakePics()
        
    if init :
        init=0
        logger.info('init')
        sendminimail('init  ')
        
