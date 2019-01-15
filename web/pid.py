# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from init import app,socketio
import commands
import time
header='''
<!DOCTYPE html>
<html>
<script type="text/javascript" src="static/socket.io.min.js"></script>
<script type="text/javascript" charset="utf-8">
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    //socket.on('connect', function() {
    //    socket.emit('my event', {data: 'I\'m connected!'});
    //});

    socket.on('pid_d', function (data) {
        console.log(data);
	document.getElementById("fname").value=data['pid_d']
        //socket.emit('my other event', { my: 'data' });
    });
</script>

<style>
th, td {
  padding: 5px;
}
th {
  text-align: left;
}
</style>

<body>
<table>
'''

param_tpl='''
<script type="text/javascript" charset="utf-8">
socket.on('{nm}', function (data) {{
	document.getElementById("{nm}").value=data
    }});
</script>
<tr>
<th>{nm}</th>
<th>
<button type="button" onclick="socket.emit('pid', '{nm}|tosend={nm}')">get</button>
<button type="button" onclick="socket.emit('pid', '{nm}|{nm}+='+document.getElementById('{nm}_step').value+';tosend={nm}')">+</button>
<button type="button" onclick="socket.emit('pid', '{nm}|{nm}-='+document.getElementById('{nm}_step').value+';tosend={nm}')">-</button>
<input type="text" id="{nm}">
Step:
<input type="text" id="{nm}_step" value="0.01">
</th>
</tr>
'''
footer='''
</table>
</body>
</html>
'''

def render():
    ret = header
    for n in [\
	'ud_pid.P',
	'ud_pid.I',
	'ud_pid.D',
	'ud_pid.initial_i',
	'ud_pid.FF',
	'lr_pid.P',
	'lr_pid.I',
	'lr_pid.D',
	'fb_pid.P',
	'fb_pid.I',
	'fb_pid.D',
	'yaw_pid.P',
	'yaw_pid.I',
	'yaw_pid.D',
	'yaw_pid.FF',
	]:
        ret += param_tpl.format(
                nm=n,
                )
    ret += footer
    return ret


@app.route('/pid')
def pid():
    return render() 

@socketio.on('pid')
def handle_message(message):
    print('received message: ' , message)
    val_id,tosend=message.split('|',1)
    commands.send(tosend.encode())
    ret=commands.recv()
    print('recived',ret)
    socketio.emit(val_id, ret) 
    
    #socketio.emit('pid_d', { 'pid_d': 'world' }) 
#def render_param(param):

