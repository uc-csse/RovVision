# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from init import app,socketio
import commands
import time
header='''
<!DOCTYPE html>
<html>
<script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/socket.io/1.3.6/socket.io.min.js"></script>
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
<body>
'''

param_tpl='''
<script type="text/javascript" charset="utf-8">
socket.on('{val}', function (data) {{
	document.getElementById("{val}").value=data
    }});
</script>
{name}
<button type="button" onclick="socket.emit('pid', '{val}|{eq}')">=</button>
<button type="button" onclick="socket.emit('pid', '{val}|{pl}')">+</button>
<button type="button" onclick="socket.emit('pid', '{val}|{mn}')">-</button>
<input type="text" id="{val}">
step:
<input type="text" id="{val_step}" value="0.01">
<br/>
'''
footer='''
</body>
</html>
'''

def render():
    ret = header
    ret += param_tpl.format(
            name='ud pid P',
            eq="tosend=ud_pid.P",
            pl="tosend=ud_pid.P;ud_pid.P+=0.01",
            mn="tosend=ud_pid.P;ud_pid.P-=0.01",
            val='ud_pid_P',
            val_step='ud_pid_step_P',
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

