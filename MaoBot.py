import sys
import socket
import string
import os
import time
from random import shuffle
from collections import deque

ops=('ruler501',)
halfops=('CelloMello','ruler')
userlist=[]

ourNick = 'MaoBot' #define nick
debug = False # For debug Mode
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

print globals()

def sendMessage(message):
	irc.send('PRIVMSG ' + chan + ' :' + message + '\r\n') #Send a warning message

def sendNotice(nick, message):
		irc.send('NOTICE ' + nick + ' :' + message + '\r\n') #Send a warning message

class Player:
	def __init__(self, nick):
		self.Hand = deque()
		self.nick = nick
	
	def deal(self, card):
		self.Hand.append(card)
		sendNotice(self.nick, "You have been dealt a "+card[1]+' of '+card[0])
		
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

def handleWrongCall(target, iteration, Log):
	print Log
	print iteration
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
			PlayerDict[lastAction[1].split()[0]].deal(deck[0])
			deck.popleft()
	
		
def callRule(nick, message):
	if len(message.split()) < 2:
		sendNotice(nick, "Malformed command. Use !call <target> <rule>")
		return
	if not nick in Players:
		sendNotice(nick, "You have no power here")
		return
	target = message.split()[0]
	rule = message[1+len(target):]
	if target in Players:
		if rule.lower().find('wrong card') != -1 or rule.lower().find('bad card') != -1 or rule.lower().find('out of turn') != -1:
			sendMessage(target+' gets his card back')
			PlayerDict[target].deal(playedCards[-1])
			playedCards.pop()
		if rule.lower().find('wrong call') != -1 or rule.lower().find('bad call') != -1:
			handleWrongCall(target, 0, list(ActionLog))
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
		sendMessage(target+' gets a nice new card')
		PlayerDict[target].deal(deck[0])
		deck.popleft()
		ActionLog.append((nick,message))
		while len(ActionLog) > 25:
			ActionLog.popleft()
	else:
		sendMessage('No player named ' + target)
	rule = message.split()[1]
	
def joinGame(nick, message):
	if not nick in Players:
		Players.append(nick)
		PlayerDict[nick]=Player(nick)
		for i in xrange(5):
			if len(deck) < 1:
				for card in playedCards:
					deck.append(card)
					if len(playedCards) < 3:
						break
				if len(deck) < 5+len(Players):
					for card in baseDeck:
						deck.append(card)
				shuffle(deck)
			PlayerDict[nick].deal(deck[0])
			deck.popleft()
		sendMessage('Welcome to Mao ' + nick + ' the only known rule is do not discuss the rules')
	else:
		sendMessage('You are already in the game')

def leaveGame(nick, message):
	if nick in Players:
		for card in PlayerDict[nick].Hand:
			deck.append(card)
		shuffle(deck)
		Players.remove(nick)
		del PlayerDict[nick]
		sendMessage('Thank You for Playing')
	else:
		sendMessage('You must join a game to quit')

def viewHand(nick, message):
	if not nick in Players:
		sendMessage('You are not in a game of Mao. Please join first.')
		return
	sendNotice(nick, PlayerDict[nick].formatHand())
	
def playCard(nick, message):
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
	
def killSelf(nick, message):
	if nick in ops:
		return 666
	else:
		sendMessage('You have no power here')

def drawCard(nick, message):
	if nick in Players:
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
		sendMessage
		PlayerDict[nick].deal(deck[0])
		deck.popleft()

def startGame(nick, message):
	for player in Players:
		if len(PlayerDict[player].Hand) != 5:
			for card in PlayerDict[nick].Hand:
				deck.append(card)
			PlayerDict[nick].Hand=deque()
			shuffle(deck)
			for i in xrange(5):
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
				PlayerDict[nick].deal(deck[0])
				deck.popleft()
	sendMessage('The game of Mao begins now')
	sendMessage('The first card is a '+deck[0][1]+' of '+deck[0][0])
	deck.popleft()

def turnOrder(nick, message):
	sendNotice(nick, ' ,'.join(Players))
		
def cardsLeft(nick, message):
	if len(message.split()) < 1:
		sendNotice(nick, "Malformed Command")
		return
	target=message.split()[0]
	if target in Players:
		sendNotice(nick, str(len(PlayerDict[target].Hand))+' cards left')

def allCardsLeft(nick, message):
	for target in Players:
		sendNotice(nick, target + ' has ' + str(len(PlayerDict[target].Hand))+' cards left')
		
def help(nick, message):
	sendNotice(nick, '!join for joining a game')
	sendNotice(nick, '!call <target> <rule> for calling someone on breaking a rule')
	sendNotice(nick, 'wrong/bad card or out of turn gives someone their card back and gives them another card')
	sendNotice(nick, 'wrong/bad call reverses the last call by target and gives them a card')
	sendNotice(nick, "!view pm's you with your current hand")
	sendNotice(nick, '!quit has you leave the current game')
	sendNotice(nick, '!play <number> of <suit> plays that card. It is case sensitive')
	sendNotice(nick, '!draw gives you a card')
	sendNotice(nick, '!start creates a new game')
	sendNotice(nick, '!order the order of players by join time')
	sendNotice(nick, '!count <target> tells you how many cards the player has left')
	sendNotice(nick, '!countAll tells you how many cards each person in the game has left')

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
	'count'		: cardsLeft,
	'countAll'	: allCardsLeft,
	}

privCommands={'kill' : killSelf}

def runBot():
	irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Define  IRC Socket
	irc.connect((network,port)) #Connect to Server
	print irc.recv ( 4096 )
	irc.recv (4096) #Setting up the Buffer
	irc.send('NICK ' + ourNick + '\r\n') #Send our Nick(Notice the Concatenation)
	irc.send('USER LEAP LEAPer LEAPer :LEAP IRC\r\n') #Send User Info to the server
	while True: #While Connection is Active
		data = irc.recv (4096) #Make Data the Receive Buffer
		print data #Print the Data to the console(For debug purposes)
		if data.find('PING') != -1: #If PING is Found in the Data
			irc.send('PONG ' + data.split()[1] + '\r\n') #Send back a PONG
		if data.find('End of /MOTD command.') != -1: #check for welcome message
			irc.send('JOIN ' + chan + '\r\n') # Join the pre defined channel
		if data.split()[1] == 'PRIVMSG': #IF PRIVMSG is in the Data Parse it
			message = ':'.join(data.split (':')[2:]) #Split the command from the message
			if data.split()[2] == chan: #Checking for the channel name
				nick = data.split('!')[ 0 ].replace(':','') #The nick of the user issueing the command is taken from the hostname
				if nick.find(OmnomIRC) != -1:
					continue
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
							irc.send('PRIVMSG chanserv :OP '+nick+'\r\n')#make auto ops ops
					for halfop in halfops:
						if nick == halfop:#see if the person is supposed to ba a halfop
							print "be a halfop"
							irc.send('PRIVMSG chanserv :HALFOP '+nick+'\r\n')#make auto half ops halfops
				if finalmessage[0] == '!':
					command = finalmessage[1:].split(' ')[0]
					if command in commands.keys():
						test = commands[command](nick, finalmessage[2+len(command):])
						if test == 666:
							break
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
							irc.send('PRIVMSG chanserv :OP '+nick+'\r\n')#make auto ops ops
					for halfop in halfops:
						if nick == halfop:#see if the person is supposed to ba a halfop
							print "be a halfop"
							irc.send('PRIVMSG chanserv :HALFOP '+nick+'\r\n')#make auto half ops halfops
				if finalmessage[0] == '!':
					command = finalmessage[1:].split(' ')[0]
					if command in privCommands.keys():
						test = privCommands[command](nick, finalmessage[2+len(command):])
						if test == 666:
							break
			else:
				print '.'+data.split()[2]+'.'
				
runBot()