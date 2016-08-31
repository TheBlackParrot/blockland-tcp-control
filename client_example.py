from socket import *;
import threading;
import hashlib;

HOST = None
PORT = None
while not HOST:
	HOST = input('HOSTNAME/IP ADDRESS [default 127.0.0.1]: ');
	if not HOST:
		HOST = "127.0.0.1";

while not PORT:
	PORT = input('PORT [default 27000]: ');
	if not PORT:
		PORT = 27000;

BUFSIZ = 2048
ADDR = (str(HOST), int(PORT));

sock = socket(AF_INET, SOCK_STREAM);
sock.connect(ADDR);


auth = None;
while not auth:
	username = input('USERNAME: ');
	# todo: password input hidden/asterisks
	password = input('PASSWORD: ');

	hash_str = hashlib.sha1(str.encode("{}:{}".format(username, password))).hexdigest();

	sock.send(str.encode("{}\tPING".format(hash_str) + "\n"));
	
	data = sock.recv(BUFSIZ).decode('utf-8');
	if data == "OK":
		print("WELCOME.");
		auth = hash_str;
	elif int(data.split(" ")[1], 16) == 0xa1:
		print("0xa1 -- INVALID CREDENTIALS");
	elif int(data.split(" ")[1], 16) == 0xa0:
		print("NO CREDENTIALS SET. Please use /tcphash [username] [password] on your Blockland server.");


class listener(object):
	def __init__(self):
		self.isRunning = True;

	def forever(self):
		global sock;

		while self.isRunning:
			data = sock.recv(BUFSIZ);

			if not data:
				break;

			print(data.decode('utf-8'));

class writer(object):
	def __init__(self):
		self.isRunning = True;

	def forever(self):
		global sock;

		while self.isRunning:
			data = input('> ');

			if not data:
				continue;
			
			parsed = data.split("\\t");
			parsed.insert(0, auth);

			sock.send(str.encode("\t".join(parsed) + "\n"));

l = listener();
thread_listener = threading.Thread(target = l.forever);
w = writer();
thread_writer = threading.Thread(target = w.forever);
thread_listener.start();
thread_writer.start();