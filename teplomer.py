#!/usr/bin/python3
import time,serial

logCtrlFile = '/tmp/kotelnik.log'
logTempFile = '/tmp/teplomerTemps.log'

class connectionError(RuntimeError):
	def __init__(self, arg):
		self.args = arg
class sensorError(RuntimeError):
	def __init__(self, arg):
		self.args = arg

def logCtrl(str):
	file = open(logCtrlFile,'a')
	file.write(str)
	file.write("\n")
	file.close()

def logTemp(str):
	file = open(logTempFile,'a')
	file.write(str)
	file.write("\n")
	file.close()
	
def readSens(retLin=False):
	ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=20)
	line= ser.readline()
	line= ser.readline()
	if retLin:
		return line
	ser.close()
	sens_str = line.decode('utf8')				# preveduje na string
	sens_str = sens_str.strip('\x00')			# zbavim se patogennich nul, ale nevim, kde se berou
	sens = sens_str.split(' ')				# rozdelim je podle mezer
	if len(sens) < 5: 					# mam-li mene radku, asi se zrovna Atmel resetuj
		raise sensorError('Dostal jsem malo dat.',sens)
	del(sens[-1])						# odstranim odradkovani
	return [int(s) for s in sens]				# prevedu na cislo

class mTime:
	def __init__(self,_h,_m):
		self.h=_h
		self.m=_m

	def isLess(self,h,m): # tento cas uz byl, oproti zadanemu
		return self.h < h or (self.h == h and self.m < m)

	def isGreater(self,h,m):	# tento cas teprve bude oproti zadanemu
		return self.h > h or (self.h == h and self.m > m)

class mDay:
	def __init__(self):
		self.filledStart = False
		pass

	def setStartTime(self,h,m):
		setattr(self,'start',mTime(h,m))
		self.filledStart = True

	def setStopTime(self,h,m):
		setattr(self,'stop',mTime(h,m))
		self.filledStop = True

	def setStartStop(self,h,m,hh,mm):
		setattr(self,'start',mTime(h,m))
		setattr(self,'stop',mTime(hh,mm))
		self.filledStart = True
		self.filledStart = True

	def isTimeForHeating(self):
		if not (self.filledStart and self.filledStart):
			return False
		h = time.localtime().tm_hour
		m = time.localtime().tm_min
		return self.start.isLess(h,m) and self.stop.isGreater(h,m)

class mWeek:
	def __init__(self):
		self.days=[mDay() for i in range(0,7)]
	
	#def getDay(self,index):
	#	return self.days[index]

	def isTimeForHeating(self):
		day = self.days[time.localtime().tm_wday]
		return day.isTimeForHeating()

class Teplomer:
	def __init__(self):
		self.vref = 5.0
		self.temperatures = [15.0 for i in range(0,4)]
		self.work = False
	
	def refreshTemperature(self):
		try:
			sens = readSens()
		except (sensorError) as e:
			logCtrl(time.strftime('%d.%m.%Y %H:%M')+' refreshTemperature() Exception: '+str(e))
			return
		rawTemps = [s/2.56*self.vref-273 for s in sens] # prepocet napeti z LM335
		self.temperatures = [t for t in rawTemps]
		
	def readVoltage(self):
		try:
			sens = readSens()
		except (sensorError) as e:
			logCtrl(time.strftime('%d.%m.%Y %H:%M')+' refreshTemperature() Exception: '+str(e))
			return
		voltage = [s/256*self.vref for s in sens]
		return voltage
	
	def doYourWork(self):
		self.work = True
		cycles = 0
		while(self.work):
			#self.refreshTemperature()
			#if cycles % 10 == 0:
			#	self.controlBoiler()
			readSens(True)
			cycles += 1
			time.sleep(60)	
	
	def cancelWork(self):
		self.work = False

if __name__ == '__main__':
	#print('Pokus: uvidime, co zmuzeme s kotelnikem.')
	t=Teplomer()
	print(t.readVoltage())
	t.refreshTemperature()
	#t.doYourWork()
	print(t.temperatures)
