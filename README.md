# kollekTOURmat

## Hamburger Geschichte(n) 

Hamburgs historische Ansichten lassen sich an Originalschauplätzen auf einem circa einstündigen Rundgang entdecken.
Dies ist die Software dazu, programmiert für einen raspberry pi mit angeschlossenem GPS Empfänger und mobilem Drucker.

### Installation 
Folgende Pakete werden benötigt:
```
sudo apt-get install python-pip gpsd gpsd-clients```
```

Außerdem wird noch das Modul configparser benötigt:
```
sudo pip install -v configparser
```

Ohne angeschlossene GPS-Gerät muss in der Datei kollekTOURmat.py die Variable debug auf 1 gestellt werden:

```
debug=1
```
