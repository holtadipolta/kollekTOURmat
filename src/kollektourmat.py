#! /usr/bin/python
 
import os
import math
from time import *
import time
import commands

#fuer gpio
import RPi.GPIO as GPIO
#fuer gps:
from gps import *
import threading
#fuer configparser
from configparser import ConfigParser

# import random module
import random

#Globale Variablen
debug=1	                #Debugmodus: 0=aus, 1=an
data = dict()           #Daten fuer die Werte aus der KonfigDatei
maxdistance = 40.00     #Zielentfernung in Metern
actual_lat=53.554022    #Startwert fuer aktuelle Latitude
actual_lon=9.99215      #Startwert fuer aktuelle Longitude
gpsd = None 		#fuer gpsd
gpsp=None
parser = ConfigParser() #Konfigurationsparser
KonfigFile="Tour.ini"	#Konfigurationsdatei
LED_RUN=4               #GPIO PORT4:  Programm gestartet 
LED_GPSDATA=17		#GPIO PORT17: Valide GPS-Daten werden empfangen 
LED_POSITION=27		#GPIO PORT27: Tour-Punkt wurde erreicht
SWITCH_PRINT=22		#GPIO Port22: Taster zum Bild Ausdruck


#GPS Klasse
class GpsPoll(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd 
    gpsd = gps(mode=WATCH_ENABLE) #GPS Stream initialisieren
    self.current_value = None
    self.running = True #Thread starten
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #neuen GPS Datensatz holen


#Alle Sections und Namen/Werte einlesen
def readConfig():
    for section in parser.sections():
        #print(section)
        data[section] = {}
        data[section]["Daten"] = {}
        data[section]["Daten"]["Longitude"] = parser.get(section, 'Longitude')
        parser.remove_option(section,'Longitude')
        data[section]["Daten"]["Latitude"] = parser.get(section, 'Latitude')
        parser.remove_option(section,'Latitude')
        data[section]["Daten"]["Ordner"] = parser.get(section, 'Ordner')
        parser.remove_option(section,'Ordner')
        data[section]["Bilder"]= {} 
        for name, value in parser.items(section):
			    print(section +":"+ name + " = " + value)
			    data[section]["Bilder"][name] = value
    return

#Feststellen welchen Radius die Stationspunkte zur aktuellen gps-Position haben
def gpsradius(x, y):
    lat1 =x
    lon1 = y
    lat2 = actual_lat
    lon2 = actual_lon
    radius = 6371000 # meter
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
	            * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d

def printBild(Datei):
    print("gedruckt wird: {}".format(Datei))
    GPIO.output(LED_RUN,GPIO.HIGH)
    #PRINT Befehl lpr
    cmd = "/usr/bin/lpr " + Datei 
    commands.getoutput(cmd)
    time.sleep(5)
    GPIO.output(LED_RUN,GPIO.LOW)
	
def main(argv):
	#Los gehts:
	global actual_lat
	global actual_lon
	#GPIO initialisieren
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(LED_RUN,GPIO.OUT)
	GPIO.setup(LED_GPSDATA,GPIO.OUT)
	GPIO.setup(LED_POSITION,GPIO.OUT)
	GPIO.setup(SWITCH_PRINT,GPIO.IN)
	#Alle Ausgaenge aus:
	GPIO.output(LED_GPSDATA,GPIO.LOW)
	GPIO.output(LED_POSITION,GPIO.LOW)
	GPIO.output(LED_RUN,GPIO.LOW)
	time.sleep(3)

	#Konfigurationsdatei lesen
	parser.read(KonfigFile)
	if not debug:
		global gpsp
		gpsp = GpsPoll() # Thread starten
	readConfig()
	#print data

	if not debug:
		try:
			gpsp.start()

		except (KeyboardInterrupt, SystemExit): #ctrl+c?
			print "\nKilling Thread..."
			gpsp.running = False
			gpsp.join() # thread beenden
    
	time.sleep(3)
	while True:
		#Programm lauuft -> LED-RUN einschalten
		GPIO.output(LED_RUN,GPIO.HIGH)
		GPIO.output(LED_GPSDATA,GPIO.LOW)
		time.sleep(3)
		if not debug:
			#GPS Daten aktualisieren
			actual_lat=gpsd.fix.latitude
			actual_lon=gpsd.fix.longitude	
		else:
			#GPS Daten werdden von Punkt1 uebernommen
			actual_lat=float(data["Punkt1"]["Daten"]["Latitude"])
			actual_lon=float(data["Punkt1"]["Daten"]["Longitude"])
			#LED-GPSDATA an, Rest aus				
			GPIO.output(LED_RUN,GPIO.LOW)
			GPIO.output(LED_POSITION,GPIO.LOW)
			GPIO.output(LED_GPSDATA,GPIO.HIGH)
			time.sleep(3)
				
		while float(actual_lat) > 1.0  and str(actual_lat)[0] !="n" : # Schleife solange valide Daten empfangen werden.	
		
			if not debug:
				#GPS Daten innerhalb der Schleife aktualisieren
				actual_lat=gpsd.fix.latitude
				actual_lon=gpsd.fix.longitude	
		
		
			print ("Valide Daten empfangen: {:f}".format(actual_lat))
			print ("-----------------------\n")
			time.sleep(1)
			printFlag = False
			#Auswertung der Datensaetze
			for datensatz in data:
				#Entfernung von aktueller Pos. ermitteln
				distance=gpsradius(float(data[datensatz]["Daten"]["Latitude"]),float(data[datensatz]["Daten"]["Longitude"])) 
				print ("Entfernung von {}: {:.2f}m".format(datensatz, distance))
			
				#Befinden wir uns  an einem Punkt?
				if (distance <= maxdistance):
						#LED-Postition an, Rest aus
						GPIO.output(LED_RUN,GPIO.LOW)
						GPIO.output(LED_GPSDATA,GPIO.LOW)
						GPIO.output(LED_POSITION,GPIO.HIGH)
						printFlag = True
						print ("Punkt {} ist naeher als {:.2f} m:  -> Abstand: {:.2f}m".format(datensatz,maxdistance,distance))
						#Anzahl der verf. Bilder ermitteln
						AnzBilder=len(data[datensatz]["Bilder"])
						#Zufallszahl ermitteln
						random.seed()
						Bildnummer = random.randint(1,AnzBilder)
						Bild="bild{}".format(Bildnummer)
						#Pfad des Bildes und Namen ermitteln
						Datei=data[datensatz]["Daten"]["Ordner"] + data[datensatz]["Bilder"][Bild]
						print (" {} Bilder verfuegbar.  Bild{} wurde ausgesucht: {} \n".format(AnzBilder, Bildnummer,data[datensatz]["Bilder"][Bild]))
						value = GPIO.input(SWITCH_PRINT)
						if not value: #Taster gedrueckt?
							 GPIO.output(LED_POSITION,GPIO.LOW)
							 time.sleep(0.5)
							 #Bild ausdrucken
							 printBild(Datei)
					    
			
			if not  printFlag :	
				#LED-GPSDATA an, Rest aus				
				GPIO.output(LED_RUN,GPIO.LOW)
				GPIO.output(LED_POSITION,GPIO.LOW)
				GPIO.output(LED_GPSDATA,GPIO.HIGH)
		
		time.sleep(5)
		print("Keine validen Daten empfangen")

	
GPIO.cleanup()                  ## Cleanup


if __name__ == "__main__":
    main(sys.argv)

