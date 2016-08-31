function GameConnection::_TCPC_getRank(%this) {
	if(%this.bl_id == getNumKeyID() || %this.bl_id == 999999) {
		return 3;
	} else if(%this.isSuperAdmin) {
		return 2;
	} else if(%this.isAdmin) {
		return 1;
	}

	return 0;
}

function _TCPC_findPlayer(%line) {
	if(getField(%line, 2) $= "ID") {
		%target = findClientByBL_ID(getField(%line, 3));
		%reason = getField(%line, 4);
	} else {
		%target = findClientByName(getField(%line, 2));
		%reason = getField(%line, 3);
	}

	return %target TAB %reason;
}