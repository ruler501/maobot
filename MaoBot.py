import sys
import socket
import string
import os
import time
import asyncore
from base64 import b64encode
from random import shuffle
from collections import deque

ops=('ruler501',)
halfops=('CelloMello','ruler')
userlist=[]

ourNick = 'MaoBot' #define nick
Debug = True # For debug Mode
network = 'efnet.port80.se' #Define IRC Network
port = 6667 #Define IRC Server Port
chan='#omnimaga-games'

ActionLog=deque()
Players=[]
PlayerDict={}
Order=False

baseDeck = []
cards=('2','3','4','5','6','7','8','9','10','Jack','Queen','King','Ace')
suits=('Spades', 'Clubs', 'Diamonds', 'Hearts')
for suit in suits:
	for card in cards:
		baseDeck.append((suit,card))
deck = deque(baseDeck)
shuffle(deck)
playedCards = deque()
singleSend=True

connections = (('efnet.port80.se', 6667), ('irp.irc.omnimaga.org', 6667))
messageQueue = []
privQueue = [[]]*(len(connections)+1)

def queueMessage(message, pid=-1, private=False):
	if pid >= 0:
		privQueue[pid].append(message)
	else:
		messageQueue.append(([0]*len(connections), message))

def sendMessage(message):
	queueMessage('PRIVMSG ' + chan + ' :' + message + '\r\n')

def sendNotice(nick, message, pid):
		queueMessage('NOTICE ' + nick + ' :' + message + '\r\n', pid)

class Player:
	def __init__(self, nick):
		self.Hand = deque()
		self.nick = nick
	
	def deal(self, card, pid):
		self.Hand.append(card)
		sendNotice(self.nick, "You have been dealt a "+card[1]+' of '+card[0], pid)
		
	def play(self, card):
		self.Hand.remove(card)
		playedCards.append(card)
		
	def removeLast(self):
		deck.append(self.Hand[-1])
		shuffle(deck)
		self.Hand.pop()
		
	def formatHand(self):
		result = ''
		for card in self.Hand:
			result += ', '+card[1]+' of '+card[0]
		return result[2:]

def giveCard(target, pid):
	if len(deck) < 1:
		for card in playedCards:
			deck.append(card)
			playedCards.remove(card)
			if len(playedCards) < 3:
				break
		if len(deck) < 5+len(Players):
			for card in baseDeck:
				deck.append(card)
		shuffle(deck)
	PlayerDict[target].deal(deck[0], pid)
	deck.popleft()
		
def handleWrongCall(target, iteration, Log):
	if len(Log) < 1:
		sendMessage('Internal error')
		return
	i=-1
	for action in Log[::-1]:
		if action[0] == target:
			lastAction=action
			break
		i-=1
	else:
		sendMessage(target+' has not called anything')
		return
	if lastAction[1].find('bad call') != -1 or lastAction[1].find('wrong call') != -1:
		handleWrongCall(lastAction[1].split()[0], iteration+1, Log[:i])
	if lastAction[1].split()[0] in Players:
		if iteration%2 == 0:
			PlayerDict[lastAction[1].split()[0]].removeLast()
		else:
			giveCard(lastAction[1].split()[0], pid)
	
		
def callRule(nick, message, pid):
	if len(message.split()) < 2:
		sendNotice(nick, "Malformed command. Use !call <target> <rule>", pid)
		return
	if not nick in Players:
		sendNotice(nick, "You have no power here", pid)
		return
	target = message.split()[0]
	rule = message[1+len(target):]
	if target in Players:
		if rule.lower().find('wrong card') != -1 or rule.lower().find('bad card') != -1 or rule.lower().find('out of turn') != -1:
			sendMessage(target+' gets his card back')
			PlayerDict[target].deal(playedCards[-1], pid)
			playedCards.pop()
		if rule.lower().find('wrong call') != -1 or rule.lower().find('bad call') != -1:
			handleWrongCall(target, 0, list(ActionLog))
		sendMessage(target+' gets a nice new card')
		giveCard(target, pid)
		ActionLog.append((nick,message))
		while len(ActionLog) > 25:
			ActionLog.popleft()
	else:
		sendMessage('No player named ' + target)
	
def joinGame(nick, message, pid):
	if not nick in Players:
		Players.append(nick)
		PlayerDict[nick]=Player(nick)
		for i in xrange(5):
			giveCard(nick, pid)
		sendMessage('Welcome to Mao ' + nick + ' the only known rule is do not discuss the rules')
	else:
		sendMessage('You are already in the game')

def leaveGame(nick, message, pid):
	if nick in Players:
		for card in PlayerDict[nick].Hand:
			deck.append(card)
		shuffle(deck)
		Players.remove(nick)
		del PlayerDict[nick]
		sendMessage('Thank You for Playing '+nick)
	else:
		sendMessage('You must join a game to quit')

def viewHand(nick, message, pid):
	if not nick in Players:
		sendMessage('You are not in a game of Mao. Please join first.')
		return
	sendNotice(nick, PlayerDict[nick].formatHand(), pid)
	
def playCard(nick, message, pid):
	if(len(message.split()) < 3):
		sendMessage("Malformed play")
		return
	playedCard=(message.split()[2],message.split()[0])
	if nick in Players:
		if playedCard in PlayerDict[nick].Hand:
			PlayerDict[nick].play(playedCard)
		else:
			sendMessage('You do not have that card')
	else:
		sendMessage('You are not in a game of Mao. Please join first.')
	
def killSelf(nick, message, pid):
	if nick in ops:
		sys.exit()
	else:
		sendMessage('You have no power here')

def drawCard(nick, message, pid):
	if nick in Players:
		giveCard(nick, pid)

def startGame(nick, message, pid):
	for player in Players:
		if len(PlayerDict[player].Hand) != 5:
			for card in PlayerDict[nick].Hand:
				deck.append(card)
			PlayerDict[player].Hand=deque()
			shuffle(deck)
			for i in xrange(5):
				giveCard(player, pid)
	sendMessage('The game of Mao begins now')
	sendMessage('The first card is a '+deck[0][1]+' of '+deck[0][0])
	deck.popleft()
	
def giveCards(nick, message, pid):
	if len(message.split()) < 2:
		sendNotice(nick, 'Malformed Call', pid)
		return
	if nick in Players:
		target = message.split()[0]
		count = int(message.split()[1])
		if target in Players:
			for i in xrange(count):
				giveCard(target, pid)
	
def turnOrder(nick, message, pid):
	sendNotice(nick, ', '.join(Players), pid)
		
def cardsLeft(nick, message, pid):
	if len(message.split()) < 1:
		sendNotice(nick, "Malformed Command")
		return
	target=message.split()[0]
	if target in Players:
		sendNotice(nick, str(len(PlayerDict[target].Hand))+' cards left')

def allCardsLeft(nick, message, pid):
	for target in Players:
		sendNotice(nick, target + ' has ' + str(len(PlayerDict[target].Hand))+' cards left', pid)
		
def help(nick, message, pid):
	sendNotice(nick, '!join for joining a game', pid)
	sendNotice(nick, '!call <target> <rule> for calling someone on breaking a rule', pid)
	sendNotice(nick, 'wrong/bad card or out of turn gives someone their card back and gives them another card', pid)
	sendNotice(nick, 'wrong/bad call reverses the last call by target and gives them a card', pid)
	sendNotice(nick, "!view pm's you with your current hand", pid)
	sendNotice(nick, '!quit has you leave the current game', pid)
	sendNotice(nick, '!play <number> of <suit> plays that card. It is case sensitive', pid)
	sendNotice(nick, '!draw gives you a card', pid)
	sendNotice(nick, '!give <target> <count> gives the player cards', pid)
	sendNotice(nick, '!start creates a new game', pid)
	sendNotice(nick, '!order the order of players by join time', pid)
	sendNotice(nick, 'PM me !help to see the PM only commands', pid)

def helpPM(nick, message, pid):
	sendNotice(nick, 'These are PM only commands', pid)
	sendNotice(nick, '!count <target> tells you how many cards the player has left', pid)
	sendNotice(nick, '!countAll tells you how many cards each person in the game has left', pid)

commands = {
	'join'		: joinGame,
	'call'		: callRule,
	'view'		: viewHand,
	'quit'		: leaveGame,
	'kill'		: killSelf,
	'play'		: playCard,
	'draw'		: drawCard,
	'help'		: help, 
	'start'		: startGame,
	'order'		: turnOrder,
	'give'		: giveCards,
	}

privCommands={
	'kill' 		: killSelf,
	'count'		: cardsLeft,
	'countAll'	: allCardsLeft,
	'help'		: helpPM
	}

def sendOmnom(message):
	encodedNick=b64encode("*"+message.split()[1], "-_").rstrip("=")
	encodedMessage=b64encode(':'.join(message.split(':')[1:]), "-_").rstrip("=")
	sendSocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sendSocket.connect(("omnomirc.www.omnimaga.org",80))
	ourNick=b64encode('MaoBot', "-_").rstrip("=")
	ourSig=b64encode('YvKvDXPQQlg96S45GgtaHFb8phLDF9rsDOXB7KiZxVE,', "-_").rstrip("=")
	path="http://omnomirc.www.omnimaga.org/message.php?nick="+ourNick+",&signature="+ourSig+"&message="+encodedMessage+"&channel="+encodedNick+"&id=9001"
	sendSocket.send("GET "+path+" HTTP/1.1\r\nHost: omnomirc.www.omnimaga.org\r\nContent-Type: application/x-www-form-urlencoded\r\n\r\n")
	returnData = sendSocket.recv(1024)
	sendSocket.close()
	return returnData
	

def handleOmnom(message, pid, private=False):
	if pid !=0 and singleSend and !private:
		return
	if message.split(')')[0] == '(#':
		return
	try:
		nick=message.split('<')[1].split('>')[0]
		realMessage=message.split('>')[1]
	except IndexError:
		return
	if realMessage[1] == '!':
		command = realMessage[2:].split(' ')[0]
		if private:
			if command in privCommands.keys():
				privCommands[command](nick, realMessage[3+len(command):], len(connections))
		else:
			if command in commands.keys():
				try:
					commands[command](nick, realMessage[3+len(command):], len(connections))
				except:
					return
	

class myController(asyncore.dispatcher):
	# time requestor (as defined in RFC 868)

	def __init__(self, host, port, pid):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect( (host, port) )
		self.connection=(host, port)
		self.id=pid
		self.f = open(host+'.log', 'a')

	def writable(self):
		return len(messageQueue) > 0 or len(privQueue[self.id]) > 0 or len(privQueue[len(connections)]) > 0

	def handle_connect(self):
		queueMessage('NICK ' + ourNick + '\r\n', self.id) #Send our Nick(Notice the Concatenation)
		queueMessage('USER LEAP LEAPer LEAPer :LEAP IRC\r\n', self.id) #Send User Info to the server

	def handle_expt(self):
		self.close() # connection failed, shutdown

	def handle_close(self):
		self.close()
	
	def handle_write(self):
		for i in xrange(len(messageQueue)):
			if messageQueue[i][0][self.id] == 0:
				self.send(messageQueue[i][1])
				messageQueue[i][0][self.id] = 1
		if singleSend:
			for message in messageQueue:
				if 1 in message[0]:
					messageQueue.remove(message)
		else:
			for message in messageQueue:
				if not 0 in message[0]:
					messageQueue.remove(message)
		for message in privQueue[self.id]:
			self.send(message)
		privQueue[self.id]=[]
		if len(privQueue[len(connections)])>0:
			for message in privQueue[len(connections)]:
				sendOmnom(message)
			privQueue[len(connections)]=[]
		
	def handle_read(self):
		data = self.recv (4096) #Make Data the Receive Buffer
		print >> self.f, data #Print the Data to the console(For debug purposes)
		if Debug:
			print data
		if data.find('PING') != -1: #If PING is Found in the Data
			queueMessage('PONG ' + data.split()[1] + '\r\n', self.id) #Send back a PONG
		if data.find('End of /MOTD command.') != -1: #check for welcome message
			queueMessage('JOIN ' + chan + '\r\n', self.id) # Join the pre defined channel
		if len(data.split()) < 4:
			return
		if data.split()[1] == 'PRIVMSG': #IF PRIVMSG is in the Data Parse it
			message = ':'.join(data.split (':')[2:]) #Split the command from the message
			if data.split()[2] == chan: #Checking for the channel name
				nick = data.split('!')[ 0 ].replace(':','') #The nick of the user issueing the command is taken from the hostname
				destination = ''.join (data.split(':')[:2]).split (' ')[-2] #Destination is taken from the data
				function = message.split()[0] #The function is the message split
				arg= data.split( )#FInally Split the Arguments by space (arg[0] will be the actual command
				s=0
				newmessage=''
				for ar in arg:
					if s>=3:
						newmessage+=ar
						newmessage+=' '
					s+=1
				s=0
				length=len(newmessage)-1
				finalmessage=''
				for char in newmessage:
					if s==length:
						break
					elif not s==0:
						finalmessage+=char
					s+=1
				s=0
				finalarg=[]
				for ar in arg:
					if s<3:
						finalarg.append(ar)
					else:
						finalarg.append(finalmessage)
						break
				if not nick in userlist:
					userlist.append(nick)
					for op in ops:
						if nick == op:#see if the person is supposed to be an op
							queueMessage('PRIVMSG chanserv :OP '+nick+'\r\n', self.id)#make auto ops ops
					for halfop in halfops:
						if nick == halfop:#see if the person is supposed to ba a halfop
							queueMessage('PRIVMSG chanserv :HALFOP '+nick+'\r\n', self.id)#make auto half ops halfops
				if nick.find('OmnomIRC') != -1:
						handleOmnom(finalmessage, self.id)
						return
				if finalmessage[0] == '!':
					command = finalmessage[1:].split(' ')[0]
					if command in commands.keys():
						try:
							commands[command](nick, finalmessage[2+len(command):], self.id)
						except:
							return
			elif ourNick in data.split()[2]:
				nick = data.split('!')[ 0 ].replace(':','') #The nick of the user issueing the command is taken from the hostname
				destination = ''.join (data.split(':')[:2]).split (' ')[-2] #Destination is taken from the data
				function = message.split()[0] #The function is the message split
				arg= data.split( )#FInally Split the Arguments by space (arg[0] will be the actual command
				s=0
				newmessage=''
				for ar in arg:
					if s>=3:
						newmessage+=ar
						newmessage+=' '
					s+=1
				s=0
				length=len(newmessage)-1
				finalmessage=''
				for char in newmessage:
					if s==length:
						break
					elif not s==0:
						finalmessage+=char
					s+=1
				s=0
				finalarg=[]
				for ar in arg:
					if s<3:
						finalarg.append(ar)
					else:
						finalarg.append(finalmessage)
						break
				if not nick in userlist:
					userlist.append(nick)
					for op in ops:
						if nick == op:#see if the person is supposed to be an op
							queueMessage('PRIVMSG chanserv :OP '+nick+'\r\n', self.id)#make auto ops ops
					for halfop in halfops:
						if nick == halfop:#see if the person is supposed to ba a halfop
							queueMessage('PRIVMSG chanserv :HALFOP '+nick+'\r\n', self.id)#make auto half ops halfops
				if nick.find('OmnomIRC') != -1:
						handleOmnom(finalmessage, self.id, True)
						return
				if finalmessage[0] == '!':
					command = finalmessage[1:].split(' ')[0]
					if command in privCommands.keys():
						try:
							privCommands[command](nick, finalmessage[2+len(command):], self.id)
						except:
							return

i=0
ourConnections=[]
for connect in connections:
	ourConnections.append(myController(connect[0], connect[1], i))
	i+=1

asyncore.loop()