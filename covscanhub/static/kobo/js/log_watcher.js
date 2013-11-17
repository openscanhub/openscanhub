// to start a log watcher, include this script and use following code:
// document.log_watcher = new LogWatcher(json_url, offset, task_finished);
// document.log_watcher.watch();

function getAjax() {
	try { return new XMLHttpRequest(); } catch (e) {}
	try { return new ActiveXObject('Msxml2.XMLHTTP'); } catch (e) {}
	try { return new ActiveXObject('Microsoft.XMLHTTP'); } catch (e) {}
}

function getElementById(id) {
	try { return document.getElementById(id); } catch(e) {}
	try { return document.all[id]; } catch(e) {}
	try { return document.layers[id]; } catch(e) {}
}

function GET_handler(log_watcher) {
	if (this.readyState == 4 && this.status == 200) {
		result = eval("(" + this.responseText + ")");
		getElementById('log').innerHTML += result.content;
		document.log_watcher.task_finished = result.task_finished
		document.log_watcher.offset = result.new_offset
		if ((window.pageYOffset + window.innerHeight) >= document.log_watcher.page_height) {
			window.scroll(window.pageXOffset, document.body.clientHeight);
			document.log_watcher.page_height = document.body.clientHeight;
		}
	}
}

function doWatch() {
	if (!document.log_watcher.task_finished) {
		client = getAjax();
		client.onreadystatechange = GET_handler;
		client.open('GET', document.log_watcher.json_url + '?offset=' + document.log_watcher.offset);
		client.send();
	}
	if (!document.log_watcher.task_finished) {
		setTimeout(doWatch, 5000);
	}
}

function LogWatcher(json_url, offset, task_finished) {
	this.json_url = json_url;
	this.offset = offset;
	this.task_finished = task_finished;
	this.page_height = 0;
	return this;
}

LogWatcher.prototype.watch = function() {
	doWatch();
}
