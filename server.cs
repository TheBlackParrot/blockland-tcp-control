function serverCmdTCPHash(%client, %username, %password) {
	if(%client.bl_id != getNumKeyID() && %client.bl_id != 999999) {
		return;
	}

	if(%username $= "") {
		messageClient(%client, '', "You did not specify a username or password.");
		messageClient(%client, '', "\c2/tcphash [username] [password]");
		return;
	}

	if(%password $= "") {
		messageClient(%client, '', "You did not specify a password.");
		messageClient(%client, '', "\c2/tcphash [username] [password]");
		return;		
	}

	messageClient(%client, '', "\c2Successfully set remote management login credentials.");
	messageClient(%client, '', "\c5You may change these at any time using the /tcphash command.");

	$Pref::Server::TCPC::Hash = sha1(%username @ ":" @ %password);
	export("$Pref::Server::*", "config/server/prefs.cs");

	for(%i=0;%i<TCP_Control_Clients.getCount();%i++) {
		%tclient = TCP_Control_Clients.getObject(%i);
		%tclient.disconnect();
	}
}

exec("./support.cs");

function initTCPControl() {
	$TCPC::Init = 1;

	exec("./log.cs");

	if($Pref::Server::TCPC::Hash $= "") {
		echo("[TCP] No login hash has been set. Please use /tcphash [username] [password] to set it.");
	}

	if(!isObject(TCP_Control_Server)) {
		echo("Called");
		new TCPObject(TCP_Control_Server);
		
		if(!$Pref::Server::TCP_Control_Port) {
			%port = $Pref::Server::Port - 1000;
		} else {
			%port = mFloor($Pref::Server::TCP_Control_Port);
		}
		TCP_Control_Server.listen(%port);
		echo("[TCP] Listening on port" SPC %port);
	}

	if(!isObject(TCP_Control_Clients)) {
		new ScriptGroup(TCP_Control_Clients);
	}
}
if($TCPC::Init $= "") {
	initTCPControl();
}

//
//if(!isFunction(jettisonParse)) {
//	echo("[TCP] Jettison hasn't loaded, loading it now");
//	if(isFile("Add-Ons/System_BlocklandGlass/support/jettison.cs")) {
//		exec("Add-Ons/System_BlocklandGlass/support/jettison.cs");
//		echo("[TCP] Loaded BLG's Jettison");
//	} else {
//		exec("./support/jettison.cs");
//	}
//}
//

// maaaay not need jettison

function TCP_Control_Server::onConnectRequest(%this, %ip, %socket) {
	echo("[TCP] Received connect request from" SPC %ip);
	
	%sock = new TCPObject(TCP_Control_Socket, %socket);
	%sock.ip = %ip;
	%sock.socket = %socket;
	%sock.authed = false;
	%sock.log("Connection established");

	TCP_Control_Clients.add(%sock);
}

// == [ Error code reference ] ==
// == 0xf#	General errors
// 0xff		Invalid command
// 0xfe		Invalid player/target
// 0xfd		Cannot manage host client

// == 0xa#	Auth errors
// 0xa1		Invalid login credentials
// 0xa0		Login hash hasn't been set by the host yet

// == 0x1#	Ban command errors
// 0x10		Invalid ban length

// == 0x0#	Chat command errors
// 0x00		Blank message

// == [ Command reference ] ==
// PING
// CHAT\t[msg]
// PLAYERS
// KICK\t["ID" or name]\t[ID if "ID"]\t[reason]
// BAN\t["ID" or name]\t[ID if "ID"]\t[length]\t[reason]

function TCP_Control_Socket::onLine(%this, %line) {
	// coming back to TS after months of learning other languages makes you wonder how people tolerate this language

	%line = trim(%line);

	if($Pref::Server::TCPC::Hash $= "") {
		%this.send("ERR 0xa0 NO_AUTH_SET_ON_SERVER");
		return;
	}

	if(getField(%line, 0) !$= $Pref::Server::TCPC::Hash) {
		%this.schedule(2000, send, "ERR 0xa1 BAD_AUTH");
		return;
	}

	switch$(getField(%line, 1)) {
		case "PING":
			if(!%this.authed) {
				%this.log("Authenticated successfully");
			}
			%this.authed = true;
			%this.send("OK");
			return;

		case "CHAT":
			if(getField(%line, 2) !$= "") {
				messageAll('', "\c5CONSOLE \c7(REMOTE)\c6:" SPC getField(%line, 2));
				%this.log("[CHAT]" SPC getField(%line, 2));
			} else {
				%this.send("ERR 0x00 NO_MSG");
				return;
			}
			%this.send("OK");
			return;

		case "PLAYERS":
			%this.send("PLAYER_LIST_START");
			for(%i=0;%i<ClientGroup.getCount();%i++) {
				%client = ClientGroup.getObject(%i);
				%this.send("PLAYER" TAB %client.getPlayerName() TAB %client.bl_id TAB %client.getRawIP() TAB %client._TCPC_getRank() TAB %client.getPing());
			}
			%this.send("PLAYER_LIST_END");
			%this.log("[PLAYERS]" SPC ClientGroup.getCount() SPC "players sent");
			// not sending "OK" here as the start/end commands should be enough
			return;

		case "KICK":
			%target_d = _TCPC_findPlayer(%line);
			%target = getField(%target_d, 0);
			%reason = getField(%target_d, 1);

			if(!isObject(%target)) {
				%this.send("ERR 0xfe INVALID_PLAYER");
				return;
			}

			if(%target._TCPC_getRank() == 3) {
				%this.send("ERR 0xfd CANNOT_MANAGE_HOST");
				return;
			}

			%this.log("[KICK]" SPC %target.bl_id @ ", reason:" SPC %reason);
			%target.delete(%reason);

			%this.send("OK");
			return;

		case "BAN":
			%target_d = _TCPC_findPlayer(%line);
			%target = getField(%target_d, 0);

			if(!isObject(%target)) {
				%this.send("ERR 0xfe INVALID_PLAYER");
				return;
			}

			if(%target._TCPC_getRank() == 3) {
				%this.send("ERR 0xfd CANNOT_MANAGE_HOST");
				return;
			}

			if(getField(%line, 2) $= "ID") {
				if(mFloor(getField(%line, 4)) == 0) {
					%this.send("ERR 0x10 INVALID_BAN_LENGTH");
					return;
				} else {
					%time = mFloor(getField(%line, 4));
					%reason = getField(%line, 5);
				}
			} else {
				if(mFloor(getField(%line, 3)) == 0) {
					%this.send("ERR 0x10 INVALID_BAN_LENGTH");
					return;
				} else {
					%time = mFloor(getField(%line, 3));
					%reason = getField(%line, 4);
				}
			}

			%this.log("[BAN]" SPC %target.bl_id SPC "for" SPC %time SPC "minutes, reason:" SPC %reason);
			banBLID(%target.bl_id, %time, (%reason !$= "" ? %reason : "Banned"));
			//echo("banBLID(" @ %target.bl_id @ ", " @ %time @ ", " @ (%reason !$= "" ? %reason : "Banned") @ ");");

			%this.send("OK");
			return;
	}

	%this.send("ERR 0xff INVALID_COMMAND");
}

function TCP_Control_Socket::onDisconnect(%this) {
	%this.log("Disconnected");
	%this.delete();
}

function TCP_Control_Clients::send(%this, %data) {
	if(%data $= "") {
		return false;
	}

	for(%i=0;%i<%this.getCount();%i++) {
		%tclient = %this.getObject(%i);
		if(%tclient.authed) {
			%tclient.send(%data);
		}
	}
}

package TCP_Control_Package {
	function onServerDestroyed() {
		TCP_Control_Clients.send("SERVER_SHUTDOWN");

		for(%i=0;%i<TCP_Control_Clients.getCount();%i++) {
			%tclient.disconnect();
		}
		
		TCP_Control_Clients.delete();
		TCP_Control_Server.delete();

		$TCPC::Init = "";

		parent::onServerDestroyed();
	}

	function serverCmdMessageSent(%client, %msg) {
		for(%i=0;%i<TCP_Control_Clients.getCount();%i++) {
			%tclient = TCP_Control_Clients.getObject(%i);
			if(%tclient.authed) {
				%tclient.send("CHAT\t" @ %client.getPlayerName() @ "\t" @ %client.bl_id @ "\t" @ %client.getRawIP() @ "\t" @ %msg);
			}
		}

		return parent::serverCmdMessageSent(%client, %msg);
	}

	function GameConnection::autoAdminCheck(%this) {
		if(%tclient.authed) {
			TCP_Control_Clients.send("PLAYER_JOIN" TAB %this.getPlayerName() TAB %this.bl_id TAB %this.getRawIP() TAB %this._TCPC_getRank());
		}
		return parent::autoAdminCheck(%this);
	}

	function GameConnection::onClientLeaveGame(%this) {
		if(%tclient.authed) {
			TCP_Control_Clients.send("PLAYER_LEFT" TAB %this.getPlayerName() TAB %this.bl_id TAB %this.getRawIP() TAB %this._TCPC_getRank());
		}
		return parent::onClientLeaveGame(%this);
	}
};
activatePackage(TCP_Control_Package);