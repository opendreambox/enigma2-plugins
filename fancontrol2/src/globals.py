Version = "V2.9r3"
# globale Variablen        
ZielRPM = 0
AktVLT = 0
AktPWM = 0
AktRPM = 0
AktTemp = 0
AktHDD = []
LastVLT = 0
LastPWM = 0
IntegralRPM = 0
AktERR = 0
ErrRPM = 0
FanFehler = 0
OverheatTimer = 0
Overheat = False
FanOffWait = False
Recording = False
RPMread = 0
RPMdiff = 0
FirstStart = True
RPMrunning = False
istStandbySave = False
disableHDDread = False
session = None
Box = ""
DataMinute = ""
FC2Log = []
FC2werte = [0.1, 0, 0, 0, 0, 0]
FC2stunde = ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
FC2HDDignore = []
HeadLine = "Time;Temp;RPM;VLT;PWM;HDD;Status;Temp1;Temp2;Temp3;Temp4;Temp5;Temp6;Temp7;Temp8\r\n"
TempName = [
	_("below Tunerslot 4"),
	_("near XILINX Spartan"),
	_("under the WLAN"),
	_("left of the Battery"),
	_("left near Front-CI"),
	_("left near Card-Slot"),
	_("over Security Card"),
	_("under the Fan")
]
