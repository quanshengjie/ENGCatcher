import Queue
import thread
import threading
import sys
import os.path
import requests
import json

class WriteToHTML(object):
    filepath = os.path.expanduser('~') + "/Desktop/catched"
    fileNum = 0
    ansAccuId = 0
    curAnsCount = 0
    htmlFile = None
    urlListFile = None
    ansIdListFile = None
    curURL = ""
    lock = threading.Lock()
    ansList = []

    def __init__(self):
        fn = self.filepath + "/TT_"+str(self.fileNum) + ".html"
        while os.path.isfile(fn):
            self.fileNum += 1
            fn = self.filepath + "/TT_"+str(self.fileNum) + ".html"
        if os.path.isfile("ansAccuId.txt"):
            f = open("ansAccuId.txt", "r")
            self.ansAccuId = int(f.readline())
            f.close()
        self.htmlFile = open(fn, "w")
        self.urlListFile = open(self.filepath + "/urlList.txt", "a")
        self.ansIdListFile = open(self.filepath + "/ansIdList.txt", "a")
        self.htmlFile.write("<!DOCTYPE html>\n")
        self.htmlFile.write("<html>\n<body>\n")
    def Exit(self):
        f = open("ansAccuId.txt", "w")
        f.write(str(self.ansAccuId))
        f.close()
        self.urlListFile.close()
        self.ansIdListFile.close()
        self.EndHTMLFile()
    def EndHTMLFile(self):
        self.htmlFile.write("</body>\n</html>")
        self.htmlFile.close()
        print "File " + str(self.fileNum) + " closed"
    def OpenNewHTMLFile(self):
        print "Open new file"
        self.fileNum += 1
        fn = filepath + "/TT_"+str(self.fileNum) + ".html"
        self.htmlFile = open(fn, "w")
        self.htmlFile.write("<!DOCTYPE html>\n")
        self.htmlFile.write("<html>\n<body>\n")


    def WriteFile(self, ans, url):
        self.lock.acquire()
        ans = ans.encode('ascii','ignore')
        if not ans in self.ansList:
            if url != self.curURL:
                self.curURL = url
                self.ansAccuId += 1
                self.ansList = []
                self.urlListFile.write(str(self.ansAccuId) + " : " + url + "\n")
            self.htmlFile.write("<h2> </h2>\n")
            self.htmlFile.write("<p>" + ans + "</p>\n")
            self.ansIdListFile.write(str(self.ansAccuId) + " : " + ans + "\n")
            self.ansList.append(ans)
            self.curAnsCount += 1
            if self.curAnsCount > 50:
                self.EndHTMLFile()
                self.OpenNewHTMLFile()
        self.lock.release()

class ExtractToFile(object):
    url = "http://gateway-a.watsonplatform.net/calls/url/URLGetRelations"
    apikey = "521ad0ef556dd68e1ec738588a03b33b63bc8f6f"
    queue = Queue.Queue();
    threadNum = 10
    queueMaxSize = 7000
    queueSep = threadSep = threading.Semaphore(value = queueMaxSize)
    exited = False
    threads = []
    fileWriter = WriteToHTML() 

    def Extract(self, urlTo):
        self.queueSep.acquire()
        self.queue.put(urlTo)

    def Exit(self):
        self.exited = True

    def Join(self):
        for lock in self.threads:
            lock.acquire()
        self.fileWriter.Exit()
    def doExtractThread(self, tId, lock):
        lock.acquire()
        while (self.exited != True) or (not self.queue.empty()):
            if not self.queue.empty():
                urlTo = self.queue.get()
                self.queueSep.release()
                data={'apikey' : self.apikey, 'url' : urlTo, 'outputMode' : 'json', 'showSourceText' : '1'}
                response = requests.post(self.url, data=data)
                ans = json.loads(response.text.encode('ascii','ignore'))
                for item in ans["relations"]:
                    self.fileWriter.WriteFile(item["sentence"], urlTo)
        lock.release()

    def __init__(self):
        for i in range(self.threadNum):
            lock = threading.Lock()
            t = thread.start_new_thread(self.doExtractThread, (i,lock,))
            self.threads.append(lock)



ef = ExtractToFile()
ef.Extract("https://engineering.osu.edu")
ef.Extract("https://engineering.osu.edu/honors")
ef.Extract("https://advising.engineering.osu.edu/current-students/graduation-honors-and-distinction")
ef.Exit()
ef.Join()
