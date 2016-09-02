function getSafeDateTime() {
	%data = getDateTime();

	%out = strReplace(%data, "/", "");
	%out = strReplace(%out, ":", "");
	%out = strReplace(%out, " ", "-");

	return %out;
}
$TCPC::TimeInit = getSafeDateTime();

if(!isObject(TCP_Control_LogObj)) {
	new FileObject(TCP_Control_LogObj);
}

function TCP_Control_Socket::log(%this, %data) {
	if(%data $= "") {
		return;
	}

	%file = TCP_Control_LogObj;

	%file.openForAppend("config/server/TCP_Control/logs/" @ $TCPC::TimeInit @ ".log");
	echo("[TCP]" SPC "[" @ %this.ip @ "]" SPC %data);
	messageAll('', "\c2[TCP]" SPC "\c4[" @ %this.ip @ "] \c6" SPC %data);
	%file.writeLine("[" @ getDateTime() @ "]" SPC "[" @ %this.ip @ "]" SPC %data);
	%file.close();
}