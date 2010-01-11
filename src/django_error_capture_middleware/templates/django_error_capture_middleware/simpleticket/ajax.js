$(document).ready(function(){
	$("a#more").click(function () {
		$(this).hide();
		$(this).parent().find("#less").show();
		$(this).parent().parent().next().show();
	});
	$("a#less").click(function () {
		$(this).hide();
		$(this).parent().find("#more").show();
		$(this).parent().parent().next().hide();
	});
});
// Uses a json request to change resolved on click
toggle_resolved = function (id) {
	$.getJSON("/simple/ticket/"+id+"/resolve/", function(data, code){ 
		var newstatus = "";
		if (data[0].fields.resolved) {
			newstatus = "True";
		} else {
			newstatus = "False"
		}
		$("a#resolved_"+id).text(newstatus);
	});
};
// Uses a json request to change owner based on the user logged in
take_ticket = function (id) {
	$.getJSON("/simple/ticket/"+id+"/take/", function(data, code){ 
		$("a#owner_"+id).text("{{ request.user.username }}");
	});
};
