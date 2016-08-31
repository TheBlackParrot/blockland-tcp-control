from dialog import Dialog;
import os;
import sys;
from socket import *;
import threading;
import hashlib;
import time, datetime;

# sunday, sunday, sunday!
dialog = Dialog(dialog="dialog", autowidgetsize=True);

dialog.set_background_title("Blockland Server Management");

HOST = None
PORT = None
while not HOST:
	code, HOST = dialog.inputbox("Hostname/IP of Blockland server:", init="127.0.0.1");
	if not HOST:
		HOST = "127.0.0.1";

	if code == dialog.CANCEL:
		os.system("clear");
		sys.exit();

while not PORT:
	code, PORT = dialog.inputbox("Port of TCP management backend:", init="27000");
	if not PORT:
		PORT = "27000";

	if code == dialog.CANCEL:
		os.system("clear");
		sys.exit();

BUFSIZ = 2048
ADDR = (str(HOST), int(PORT));

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


main_menu_choices = [
	("C", "Chat"),
	("P", "View Players"),
	("K", "Kick Players"),
	("B", "Ban Players"),
	("E", "Exit")
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

class listener(object):
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

l = listener();
thread_listener = threading.Thread(target = l.forever);
thread_listener.start();

keep_going = True;
while keep_going:
	l.print_lines = False;

	code, tag = dialog.menu("Main Menu", choices=main_menu_choices);
	
	if code == dialog.OK:
		if tag == "E":
			os.system("clear");
			sys.exit();

		elif tag == "C":
			global sock;
			os.system("clear");

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
	else:
		os.system("clear");
		sys.exit();

os.system("clear");
sys.exit();

'''
import atexit

@atexit.register
def goodbye():
	os.system("clear");
'''