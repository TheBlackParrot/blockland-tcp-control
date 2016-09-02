from dialog import Dialog;
import os;
import sys;
from socket import *;
import threading;
import hashlib;
import time, datetime;
from tabulate import tabulate;
import operator;

'''
3rd-party dependencies:
	- pythondialog
	- tabulate
'''


# sunday, sunday, sunday!
dialog = Dialog(dialog="dialog", autowidgetsize=True);

dialog.set_background_title("Blockland Server Management");

sock = None;
def quit():
	global sock;
	
	if sock:
		sock.disconnect();

	os.system("clear");
	sys.exit();

HOST = None
PORT = None
while not HOST:
	code, HOST = dialog.inputbox("Hostname/IP of Blockland server:", init="127.0.0.1");
	if not HOST:
		HOST = "127.0.0.1";

	if code == dialog.CANCEL:
		quit();

while not PORT:
	code, PORT = dialog.inputbox("Port of TCP management backend:", init="28001");
	if not PORT:
		PORT = "28001";

	if code == dialog.CANCEL:
		quit();

BUFSIZ = 1024
ADDR = (str(HOST), int(PORT));

setdefaulttimeout(5.0);

sock = socket(AF_INET, SOCK_STREAM);
try:
	sock.connect(ADDR);
except:
	sys.exit("Could not connect to the TCP management backend.");

auth = None;
while not auth:
	code, username = dialog.inputbox("Username:");
	if code == dialog.CANCEL:
		continue;

	# TODO: use an env variable to disable insecure mode (asterisks instead of nothing)
	code, password = dialog.passwordbox("Password:", insecure=True);
	if code == dialog.CANCEL:
		continue;

	dialog.infobox("Logging in...");

	hash_str = hashlib.sha1(str.encode("{}:{}".format(username, password))).hexdigest();

	sock.send(str.encode("{}\tPING".format(hash_str) + "\n"));
	
	data = sock.recv(BUFSIZ).decode('utf-8');
	if data == "OK":
		dialog.msgbox("Logged in successfully.");
		auth = hash_str;
	elif int(data.split(" ")[1], 16) == 0xa1:
		dialog.msgbox("Could not log in, credentials were invalid. Please try again.");
	elif int(data.split(" ")[1], 16) == 0xa0:
		dialog.msgbox("Could not log in, credentials have not been set up on the server. Please use /tcphash [username] [password] on your Blockland server to set these.");

class MessageListener():
	def __init__(self):
		global sock;
		global auth;

		# self.chat = ChatStorage();
		self.sock = sock;
		self.auth = auth;

	def prepare(self, data):
		auth = self.auth;
		data.insert(0, auth);
		return "\t".join(data);

	def send(self, data):
		try:
			sock.send(data + "\n");
			return True;
		except:
			return False;

	def fetch(self, data=None):
		sock = self.sock;

		if data:
			if type(data) != str:
				raise TypeError;

			try:
				sock.send(str.encode(data + "\n"));
			except:
				return False;

		try:
			data = sock.recv(BUFSIZ);
		except:
			return False;

		if not data:
			return False;
		else:
			data = data.decode('utf-8');

		return data;

interface = MessageListener();

main_menu_choices = [
	("C", "Chat"),
	("P", "Manage Players"),
	("E", "Exit")
];

player_management_choices = [
	("P", "View Players"),
	("K", "Kick Players"),
	("B", "Ban Players"),
	("E", "Exit Submenu")
];

class ChatStorage():
	def __init__(self, max_lines=50):
		self.max_lines = max_lines;
		self.lines = [];

	def append(self, name, message):
		self.lines.append({"name": name, "message": message, "timestamp": int(time.time())});

		if len(self.lines) > self.max_lines:
			self.lines = self.lines[1:50];

		return self.lines[-1:];

	def fetch(self, lines=25):
		if lines > self.max_lines:
			lines = self.max_lines;

		return self.lines[-lines:];

	def parse(self, data):
		name = data["name"];
		timestamp = datetime.datetime.fromtimestamp(data["timestamp"]).strftime("%H:%M:%S");
		message = data["message"];

		return "[{}] <{}> {}".format(timestamp, name, message);
'''
class ChatListener(threading.Thread):
	def __init__(self):
		self.isRunning = True;
		self.chat = ChatStorage();
		self.print_lines = False;

	def forever(self):
		global sock;
		global chat_keep_going;

		while self.isRunning:
			data = sock.recv(BUFSIZ);

			if not data:
				break;

			parts = data.decode("utf-8").split("\t");

			if parts[0] == "CHAT":
				most_recent = self.chat.append(parts[1], parts[4]);

				if self.print_lines:
					print(self.chat.parse(most_recent[0]));
'''

def get_players():
	dialog.infobox("Fetching player data...");

	global sock;

	data = interface.fetch(data=interface.prepare(["PLAYERS"]));
	print(data);

	if not data:
		return False;

	if data == "PLAYER_LIST_START":
		players = [];
		while True:
			try:
				data = interface.fetch().split("\t");
			except:
				return False;

			print(data);

			if not data:
				return False;
			if not data[0] or data[0] == "PLAYER_LIST_END":
				break;

			print("receiving player data...");

			if data[0] == "PLAYER":
				# %this.send("PLAYER" TAB %client.getPlayerName() TAB %client.bl_id TAB %client.getRawIP() TAB %client._TCPC_getRank());
				player = {
					"name": data[1],
					"bl_id": data[2],
					"ip": data[3],
					"rank": data[4],
					"ping": data[5]
				};
				players.append(player);
			else:
				return False;
	else:
		return False;

	return players;

keep_going = True;
while keep_going:
	global sock;

	code, tag = dialog.menu("Main Menu", choices=main_menu_choices);
	
	if code == dialog.OK:
		if tag == "E":
			quit();

		elif tag == "C":
			os.system("clear");
			dialog.msgbox("Work in progress.");

			'''
			l = ChatListener();
			thread_listener = threading.Thread(target = l.forever);
			thread_listener.start();

			chat_keep_going = True;
			l.print_lines = True;

			print("Use CTRL-C to leave the chat screen.\n");
			for line in l.chat.fetch():
				print(l.chat.parse(line));

			while chat_keep_going:
				try:
					data = input('[CONSOLE]> ');

					if not data:
						continue;
					
					parsed = [auth, "CHAT", data];

					sock.send(str.encode("\t".join(parsed) + "\n"));
				except KeyboardInterrupt:
					chat_keep_going = False;
					thread_listener.isRunning = False;
					del thread_listener;
			'''

		elif tag == "P":
			players_keep_going = True;

			while players_keep_going:
				code, tag = dialog.menu("Player Management", choices=player_management_choices);

				if tag == "E" or code == dialog.CANCEL:
					players_keep_going = False;
					continue;

				else:
					data = get_players();
					if not data:
						# Blockland Is Bad, Kids. (rarely sends a line without a newline character)
						dialog.msgbox("An error occurred, please try again.");
						continue;

					# P, K, B
					if tag == "P":
						os.system("clear");

						print(tabulate(data, headers="keys"));
						
						input("\nPress enter to go back.");


	else:
		quit();

quit();

'''
import atexit

@atexit.register
def goodbye():
	os.system("clear");
'''