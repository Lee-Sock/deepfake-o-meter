import time, os, smtplib, argparse, socket
import numpy as np
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader


global portSum
portSum = 10000


def createHTML(path):
    data = np.load(path+'info.npz')
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("result.j2")
    videoName = data['videoName']
    frames = data['frame_num']
    height = data['height']
    weight = data['weight']
    fps = data['fps']
    images = []
    videos = []
    methods = data['methods']
    for method in methods:
        images.append(videoName + method + '.jpg')
        videos.append(videoName + method + '.mp4')

    content = template.render(videoName=videoName, frames=frames, height=height, weight=weight, images=images,
                              videos=videos)

    with open(path+'result.py', 'w') as fp:
        fp.write(content)


def get_host_ip():
    """
    get host ip address
    :return: ip
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


# check whether the port is used by other program
def is_port_used(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def SendEmail(receiver, filedir, portSum):

    # information about the sender
    sender = 'zchh1209@163.com'
    smtpserver = 'smtp.163.com'
    username = 'zchh1209'
    password = 'UFLRRRLDPWZKJDWV'
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver

    # email title
    mail_title = 'Detection result by DeepFakeOmeter'
    message['Subject'] = Header(mail_title, 'utf-8')

    # ip for the detection result
    host_ip = get_host_ip()
    while is_port_used(host_ip, portSum):
        portSum = portSum + 1

    # email content
    Addresss = 'http://'+host_ip+':'+str(portSum)+'/'
    message.attach(MIMEText('This is the result generated by the DeepFakeOmeter.'+'\n'+
    'The username is None. And the password is your email+your pin code.' + '\n'+
    'And you can check your result: ' + Addresss
    , 'plain', 'utf-8'))

    # send email
    smtpObj = smtplib.SMTP_SSL(smtpserver)
    smtpObj.connect(smtpserver)
    smtpObj.login(username, password)
    smtpObj.sendmail(sender, receiver, message.as_string())
    print("suceed")
    smtpObj.quit()
    createHTML(filedir)
    # setup the url for detection result
    pin = np.load(os.path.join('tmp', filedir.split('/', 1)[1], 'pin.npy'))
    date = datetime.now().strftime('%Y%m%d')
    # logfile = os.path.join('tmp', filedir.split('/', 1)[1], date+'.txt')
    logfile = os.path.join('log','Log'+date+'.txt')
    with open(logfile,"a",newline = "") as f:
        f.writelines(str(portSum)+'\n')

    passwordEmail = receiver + str(pin)
    commendLine = 'updog'+' -d '+filedir+' -p ' + str(portSum) + ' --password ' + passwordEmail + ' &'
    os.system(commendLine)




class MyDirEventHandler(FileSystemEventHandler):
    def on_moved(self, event):
        print("move", event)
    def on_deleted(self, event):
        print("delete", event)
    def on_modified(self, event):
        print("modified:", event)
    def on_created(self, event):
        print("create:", event)
        filePath = event.src_path
        if os.path.isfile(filePath):
            if filePath.split('/')[-1] == 'finish.txt':
                filePathSplit = filePath.split('/')
                email = filePathSplit[2]
                filedir = filePath[2:].rsplit("/", 1)[0]

                SendEmail(email, filedir,  portSum)



if __name__ == '__main__':
    observer = Observer()
    fileHandler = MyDirEventHandler()
    observer.schedule(fileHandler, "./result", True)
    observer.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
