import json
from tkinter import *
from urllib.request import urlopen
import pycountry_convert as pc
from geopy.geocoders import Nominatim
import csv
import pymysql
from PIL import Image, ImageTk
import math
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg




continents = {
    'NA': 'North America',
    'SA': 'South America',
    'AS': 'Asia',
    'OC': 'Australia',
    'AF': 'Africa',
    'EU': 'Europe'
}

def getCountry(lat, lon):
    key = "AIzaSyDEoHaaSS-4Q1yHP8MnWqGwDBpzL_U28rc"
    url = "https://maps.googleapis.com/maps/api/geocode/json?"
    url += "latlng=%s,%s&sensor=false&key=%s" % (lat, lon, key)
    v = urlopen(url).read()
    j = json.loads(v)
    components = j['results'][0]['address_components']
    country = None
    for c in components:
        if "country" in c['types']:
            country = c['long_name']
    return  country



def getContinent(country):
    country_code = pc.country_name_to_country_alpha2(country, cn_name_format="default")
    continent_name = pc.country_alpha2_to_continent_code(country_code)
    return continents.get(continent_name)


# geolocator = Nominatim(user_agent="my_user_agent")
# city ="Cameroons"
# loc = geolocator.geocode(city)
# print("latitude is :-" ,loc.latitude,"\nlongtitude is:-" ,loc.longitude)
# print(getCountry(loc.latitude,loc.longitude))
# print(getContinent(getCountry(loc.latitude,loc.longitude)))

mydb = pymysql.connect(host='localhost',
    user='root',
    passwd='12345678',
    db = 'Test')
cursor = mydb.cursor()

#creating and delete table
# cursor.execute("DROP TABLE `Test`")
# cursor.execute("CREATE TABLE `Test` (`Year` INT(255), `FROM` VARCHAR(255), `To` VARCHAR(255),`FromLat` FLOAT(9,6),"
#                "`FromLon` FLOAT(9,6), `ToLat` FLOAT(9,6), `ToLon` FLOAT(9,6), `Trade` VARCHAR(255), "
#                "`Units` VARCHAR(255), `Amount` INT(255));")

def insertData(cursor, data): #may take a while due to google api
    cursor.execute("DROP TABLE `Test`")
    cursor.execute("CREATE TABLE `Test` (`Year` INT(255), `FROM` VARCHAR(255), `To` VARCHAR(255),`FromLat` FLOAT(9,6),"
                   "`FromLon` FLOAT(9,6), `ToLat` FLOAT(9,6), `ToLon` FLOAT(9,6), `Trade` VARCHAR(255), "
                   "`Units` VARCHAR(255), `Amount` INT(255));")
    with open(data.filename) as csv_file:
        csv_data = csv.reader(csv_file)
        geolocator = Nominatim(user_agent="my_user_agent")
        tmp = []
        for row in csv_data:
            row[0] = int(row[0])
            row[5] = int(row[5])
            fromCity = row[1]
            toCity = row[2]
            fromLoc = geolocator.geocode(fromCity)
            toLoc = geolocator.geocode(toCity)
            tmp.append(row[0])
            tmp.append(row[1])
            tmp.append(row[2])
            tmp.append(fromLoc.latitude)
            tmp.append(fromLoc.longitude)
            tmp.append(toLoc.latitude)
            tmp.append(toLoc.longitude)
            tmp.append(row[3])
            tmp.append(row[4])
            tmp.append(row[5])
            cursor.execute('INSERT INTO `Test` (`Year`, `From`, `To`, `FromLat`,`FromLon`, `ToLat`, `ToLon`, `Trade`, `Units`, `Amount`) VALUES("%s","%s","%s", "%s", "%s","%s", "%s","%s","%s","%s")',
                tmp)
            tmp=[]



def loadVoyages(data):
    cursor.execute("SELECT * FROM `Test` ORDER BY `Year`")
    myresult = cursor.fetchall()

    for voyage in myresult:
        data.importVoyages.append(voyage)

class Voyage(object):
    def __init__(self, cx, cy, endX, endY,ox, oy, info, counted, data):
        self.cx = cx
        self.cy = cy
        self.endX = endX
        self.endY = endY
        self.ox = ox
        self.oy = oy
        self.info = info
        self.counted = counted
        self.theta = math.atan(abs(data.height-self.endY-data.height+self.cy)/abs(self.endX-self.cx))#might not be correct since float


    def move(self, data):
        if abs(self.cx-self.endX)>0.5 and abs(self.cy-self.endY)>0.5:
                self.cx = self.cx + ((self.endX-self.cx)/abs(self.endX-self.cx))*(data.speed)*math.cos(self.theta)
                self.cy = self.cy + ((self.endY-self.cy)/abs(self.endY-self.cy))*(data.speed)*math.sin(self.theta)


def convertVoyages(data):
    for voyage in data.importVoyages:
        cx = ((voyage[4]+180)/360)*data.width
        cy = data.height - ((voyage[3] + 90) / 180) * data.height
        endX = ((voyage[6] + 180) / 360) * data.width
        endY = data.height -((voyage[5] + 90) / 180) * data.height
        info = [voyage[0],voyage[1],voyage[2],voyage[7],voyage[8],voyage[9]]
        data.voyages.append(Voyage(cx,cy,endX,endY,cx,cy,info, False, data))
        if voyage[9] > data.maxSize:
            data.maxSize = voyage[9]

def drawInfo(canvas, data):
    x = data.width*(8/10)
    y = data.height*(1/40)
    ex = data.width*(49/50)
    ey = data.height*(7/25)
    canvas.create_rectangle(x, y, ex, ey, fill='#fcf9e3')
    canvas.create_text(x+(1/2)*(ex-x),y+(1/7)*(ey-y), text="Year: "+str(data.selectedVoyage.info[0]), font = "Chalkboard 15 bold")
    canvas.create_text(x + (1 / 2) * (ex - x), y + (2 / 7) * (ey - y), text="From: " + data.selectedVoyage.info[1][1:len(data.selectedVoyage.info[1])-1], font = "Chalkboard 15 bold")
    canvas.create_text(x + (1 / 2) * (ex - x), y + (3 / 7) * (ey - y), text="To: " + data.selectedVoyage.info[2][1:len(data.selectedVoyage.info[2])-1], font = "Chalkboard 15 bold")
    canvas.create_text(x + (1 / 2) * (ex - x), y + (4 / 7) * (ey - y), text="Trade: " + data.selectedVoyage.info[3][1:len(data.selectedVoyage.info[3])-1], font = "Chalkboard 15 bold")
    canvas.create_text(x + (1 / 2) * (ex - x), y + (5 / 7) * (ey - y), text="Unit: " + data.selectedVoyage.info[4][1:len(data.selectedVoyage.info[4])-1], font = "Chalkboard 15 bold")
    canvas.create_text(x + (1 / 2) * (ex - x), y + (6 / 7) * (ey - y), text="Amount: " + str(data.selectedVoyage.info[5]), font = "Chalkboard 15 bold")

def initNewWorld(data):
    tmp = {}
    for voyage in data.voyages:
        country = getCountry(((data.height - voyage.endY) / data.height) * 180 - 90,
                             (voyage.endX / data.width) * 360 - 180)
        if voyage.info[3] not in tmp and getContinent(country)=="North America" or getContinent(country)=="South America":
            tmp[voyage.info[3]]=[0]
    data.newWorld = tmp
    data.newWorld["Year"] = [data.year]

def drawGraphs(root, data):
    if True:
        print(data.newWorld)
        data.df2 = DataFrame(data.newWorld, columns=['Year', "'Slaves'"]) #need to include more columns (for all key in dict)
        data.figure2 = plt.Figure(figsize=(5, 1.7), dpi=100)
        data.ax2 = data.figure2.add_subplot(111)

        data.line2 = FigureCanvasTkAgg(data.figure2, root)
        data.line2.get_tk_widget().pack(side=
                                   LEFT)
        data.ax2.set_title('New World\'s Accumulative Imports')

        data.df = DataFrame(data.newWorld, columns=['Year', "'Slaves'"])
        data.figure = plt.Figure(figsize=(5, 1.7), dpi=100)
        data.ax = data.figure.add_subplot(111)
        data.line = FigureCanvasTkAgg(data.figure, root)
        data.line.get_tk_widget().pack(side=
                                   RIGHT)
        data.ax.set_title('Old World\'s Accumulative Imports')

def initOldWorld(data):
    tmp = {}
    for voyage in data.voyages:
        country = getCountry(((data.height - voyage.endY) / data.height) * 180 - 90,
                             (voyage.endX / data.width) * 360 - 180)
        if voyage.info[3] not in tmp and getContinent(country) != "North America" and getContinent(country) != "South America":
            tmp[voyage.info[3]] = [0]
    data.oldWorld = tmp
    data.oldWorld["Year"] = [data.year]

def drawMenu(canvas, data):
    canvas.create_text(data.width / 2, 4 * data.height / 16, text="ArgoVX", font="Chalkboard 50 bold")
    canvas.create_rectangle(data.width / 3, 9*data.height / 16, 2 * data.width / 3, 11 * data.height / 16, fill="orange")
    canvas.create_text(data.width/2, 10*data.height/16, text = "Start Simulation", font="Chalkboard 28 bold")
    canvas.create_rectangle(data.width / 3, 12*data.height / 16, 2 * data.width / 3, 14 * data.height / 16, fill= "orange")
    canvas.create_text(data.width / 2, 13 * data.height / 16, text="Settings", font="Chalkboard 28 bold")

def drawSettings(canvas, data):
    canvas.create_text(data.width/2, 2*data.height/6, text="Enter File Name", font = "Chalkboard 50 bold")
    if data.selected:
        canvas.create_rectangle(data.width / 4, 3 * data.height / 6, 3 * data.width / 4, 4 * data.height / 6, outline="orange")
    else:
        canvas.create_rectangle(data.width / 4, 3 * data.height / 6, 3 * data.width / 4, 4 * data.height / 6)

    canvas.create_text(data.width / 2, 7 * data.height / 12, text=data.filename, font="Chalkboard 30 bold")
    canvas.create_rectangle(5*data.width / 12, 5 * data.height / 6, 7 * data.width / 12, 11 * data.height / 12)
    canvas.create_text(data.width/2, 21*data.height/24, text="Back", font="Chalkboard 20 bold", fill = "orange")


def init(data, root):
    data.importVoyages = []
    data.voyages = []
    #data.voyages.append(Voyage(0,0,1000,600,"info",data))
    data.speed = 0.5
    data.maxSize = 0
    data.year = 1599
    data.yearStart = 1599
    data.yearIncrement = 2
    data.yearMod = 0
    data.pause = False

    #print(data.importVoyages[0][0]-1)
    data.selectedVoyage = ""
    data.newWorld = ""

    data.oldWorld = ""

    data.pause = True
    data.scene = "Menu"
    data.root = root
    data.filename = ""
    data.selected = False





def mousePressed(event, data):
    if data.scene == "Simulation":
        for voyage in data.voyages:
            if abs(event.x-voyage.cx)<=5 and abs(event.y-voyage.cy)<=5:
                data.selectedVoyage = voyage
    elif data.scene == "Menu":
        if data.width/3<=event.x<=2*data.width/3 and 9*data.height/16<=event.y<=11*data.height/16:
            insertData(cursor, data)  # only when user want to load new data
            data.scene = "Simulation"
            loadVoyages(data)
            convertVoyages(data)
            initNewWorld(data)
            initOldWorld(data)
            drawGraphs(data.root, data)
        elif data.width/3<=event.x<=2*data.width/3 and 12*data.height/16<=event.y<=14*data.height/16:
            data.scene = "Settings"
    elif data.scene == "Settings":
        if data.width/4<=event.x<=3*data.width/4 and 3*data.height/6<=event.y<=4*data.height/6:
            data.selected = True
        elif 5*data.width/12<=event.x<=7*data.width/12 and 5*data.height/6<=event.y<=11*data.height/12:
            data.selected = False
            data.scene = "Menu"

def keyPressed(event, data):
    if data.scene == "Simulation":
        if event.keysym == "p":
            data.pause = not data.pause
        if event.keysym == "Left":
            print(data.newWorld)
            if(data.year-data.yearStart < 50):
                data.year = 1599
            else:
                data.year = data.year - 50

            for voyage in data.voyages: #temporary fix
                if data.year == voyage.info[0]:
                    data.year = data.year - 1


            for voyage in data.voyages:
                if (voyage.info[0] >= data.year):
                    voyage.counted = False
                    voyage.cx = voyage.ox
                    voyage.cy = voyage.oy
            tmp1 = []
            tmp2 = []
            for i in range(len(data.newWorld['Year'])):
                if data.newWorld['Year'][i] <= data.year:
                    tmp1.append(data.newWorld['Year'][i])
                    tmp2.append(data.newWorld["'Slaves'"][i])
            data.newWorld['Year'] = tmp1
            data.newWorld["'Slaves'"] = tmp2
            tmp1 = []
            tmp2 = []
            for i in range(len(data.oldWorld['Year'])):
                if data.oldWorld['Year'][i] <= data.year:
                    tmp1.append(data.oldWorld['Year'][i])
                    tmp2.append(data.oldWorld["'Slaves'"][i])
            data.oldWorld['Year'] = tmp1
            data.oldWorld["'Slaves'"] = tmp2


            data.figure.clf()
            data.figure2.clf()

            data.line2.get_tk_widget().pack_forget()
            data.line.get_tk_widget().pack_forget()
            drawGraphs(data.root, data)
            data.df2 = DataFrame(data.newWorld, columns=['Year', "'Slaves'"])
            data.df2 = data.df2[['Year', "'Slaves'"]].groupby('Year').sum()
            data.df2.plot(kind='line', legend=False, ax=data.ax2, color='r', marker='o', fontsize=10)
            data.df = DataFrame(data.oldWorld, columns=['Year', "'Slaves'"])
            data.df = data.df[['Year', "'Slaves'"]].groupby('Year').sum()
            data.df.plot(kind='line', legend=False, ax=data.ax, color='r', marker='o', fontsize=10)
            data.figure.canvas.draw()
            data.figure2.canvas.draw()
    elif data.scene == "Settings":
        if data.selected:
            if event.keysym=="BackSpace" and len(data.filename)!=0:
                data.filename = data.filename[:-1]
            elif event.keysym!="BackSpace":
                data.filename+=chr(event.keycode)


def timerFired(data):
    if data.scene == "Simulation":
        if data.pause == False:
            if(data.yearMod==data.yearIncrement):
                data.yearMod = 1
                data.year+=1
            else:
                data.yearMod+=1


def redrawAll(canvas, data):
    if data.scene == "Menu":
        drawMenu(canvas, data)

    elif data.scene == "Simulation":
        canvas.create_image(0, 0, image=data.img, anchor=NW) #map
        canvas.create_text(data.width * (1 / 2), data.height * (1 / 30), text=str(data.year), fill="#f56600",
                           font="Chalkboard 40 bold")
        for voyage in data.voyages:
            r = (voyage.info[5]/data.maxSize)*15
            if(voyage.info[0] <= data.year):
                if voyage.counted == False:
                    country = getCountry(((data.height - voyage.endY)/data.height)*180-90,(voyage.endX/data.width)*360-180)
                    if getContinent(country)=="North America" or getContinent(country)=="South America":

                        data.newWorld[voyage.info[3]].append(data.newWorld[voyage.info[3]][-1]+voyage.info[5])
                        data.newWorld['Year'].append(data.year)
                        voyage.counted = True
                        data.df2 = DataFrame(data.newWorld, columns=['Year', "'Slaves'"])
                        data.df2 = data.df2[['Year', "'Slaves'"]].groupby('Year').sum()
                        data.df2.plot(kind='line', legend=False, ax=data.ax2, color='r', marker='o', fontsize=10)

                        data.figure2.canvas.draw()
                        #data.figure2.canvas.flush_events()
                    else:
                        data.oldWorld[voyage.info[3]].append(data.oldWorld[voyage.info[3]][-1] + voyage.info[5])
                        data.oldWorld['Year'].append(data.year)
                        voyage.counted = True
                        data.df = DataFrame(data.oldWorld, columns=['Year', "'Slaves'"])
                        data.df = data.df[['Year', "'Slaves'"]].groupby('Year').sum()
                        data.df.plot(kind='line', legend=False, ax=data.ax, color='r', marker='o', fontsize=10)
                        data.figure.canvas.draw()
                        #data.figure.canvas.flush_events()
                for i in range(40):
                    if(i%2==0):
                        voyage.move(data)
                    else:
                        x = voyage.cx
                        y = voyage.cy
                        canvas.create_oval(x-r, y-r, x+r, y+r, fill='red')
                        voyage.move(data)
        if data.selectedVoyage != "":
            drawInfo(canvas, data)
        canvas.create_text(data.width*(1/2), data.height*(1/30), text=str(data.year), fill="#f56600", font = "Chalkboard 40 bold")
    elif data.scene == "Settings":
        drawSettings(canvas, data)





def run(width=300, height=300):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        canvas.create_rectangle(0, 0, data.width, data.height,
                                fill='white', width=0)
        redrawAll(canvas, data)
        canvas.update()

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 4 # milliseconds ~240 fps
    root = Tk()
    data.root = root
    init(data, root)
    # create the root and the canvas
    canvas = Canvas(root, width=data.width, height=data.height)
    data.canvas = canvas
    canvas.configure(bd=0, highlightthickness=0)
    canvas.pack(expand=YES, fill=BOTH)
    img = ImageTk.PhotoImage(Image.open("map.png"))
    root.img = img
    data.img = img
    #panel = Label(root, image=img)
    #panel.grid()
    #drawGraphs(root, data)
    root.resizable(False, False)
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed
    print("bye!")

run(1152, 576)
mydb.commit()
cursor.close()

