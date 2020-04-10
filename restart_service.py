
import paramiko

class ssh_restart():

    def __init__(self):
        self.nbytes = 4096
        self.port = 22
        self.username = 'pi'
        self.password = 'chickendinner'

    def remote_service_command(self, host, action, service_name):
        if action == 'restart_service':
            command = 'sudo systemctl start ' + str(service_name)

        elif action == 'restart_device':
            command = 'sudo reboot now'

        hostname = host

        ssh_client = paramiko.Transport((hostname, self.port))
        ssh_client.connect(username=self.username, password=self.password)

        stdout_data = []
        stderr_data = []
        session = ssh_client.open_channel(kind='session')
        session.exec_command(command)
        while True:
            if session.recv_ready():
                stdout_data.append(session.recv(nbytes))
            if session.recv_stderr_ready():
                stderr_data.append(session.recv_stderr(nbytes))
            if session.exit_status_ready():
                break

        print('exit status: '), session.recv_exit_status()
        print(''.join(stdout_data))
        print(''.join(stderr_data))

        session.close()
        ssh_client.close()
