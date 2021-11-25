import base64
import os
import ssl
import getpass
from socket import socket, AF_INET, SOCK_STREAM


def print_log(command, message):
    sep = '\n'
    t = list(filter(None, message.decode('utf-8').split(sep)))
    for i in range(len(t)):
        if i == 0:
            t[i] = "\t" + t[i]
        else:
            t[i] = "\t\t" + t[i]

    print(f"{command}: {str.join(sep, t)}")


def get_addr(addr: str):
    s = addr.split(":")
    if len(s) == 2:
        return s[0], int(s[1])
    else:
        return s[0], 25


class SMTPClient:
    # def __init__(self, user: str, to: str, subject: str, images: str, use_ssl: bool, smtp_server_address: str, use_auth: bool, show_verbose: bool):
    #     self.ssl_available = False
    #     self.auth_available = True
    #
    #     self.show_verbose = show_verbose
    #     self.use_auth = use_auth
    #     self.use_ssl = use_ssl
    #     self.images = images
    #     self.subject = subject
    #     self.to = to
    #     self.user = user
    #     self.smtp_server_address = smtp_server_address
    #     self.sock = None
    #
    #     self.image_dict = dict()
    #     self.image_dict['gif'] = 'gif'
    #     self.image_dict['jpeg'] = 'jpeg'
    #     self.image_dict['jpg'] = 'jpeg'
    #     self.image_dict['png'] = 'png'
    #     self.image_dict['svgz'] = 'svg+xml'
    #     self.image_dict['svg'] = 'svg+xml'
    #     self.image_dict['tif'] = 'tiff'
    #     self.image_dict['tiff'] = 'tiff'
    #     self.image_dict['ico'] = 'vnd.microsoft.icon'
    #     self.image_dict['wbmp'] = 'vnd.wap.wbmp'
    #     self.image_dict['webp'] = 'webp'

    def __init__(self, user: str, to: str, subject: str, text_file: str, use_ssl: bool, smtp_server_address: str, use_auth: bool, show_verbose: bool):
        self.ssl_available = False
        self.auth_available = True

        self.show_verbose = show_verbose
        self.use_auth = use_auth
        self.use_ssl = use_ssl
        self.text_file = text_file
        self.subject = subject
        self.to = to
        self.user = user
        self.smtp_server_address = smtp_server_address
        self.sock = None

    def throw_error(self, m: str):
        self.check_response_code_for_errors('500', "", [''], {}, m)

    def check_response_code_for_errors(
            self,
            response_code: str,
            response_message: str,
            expected_success_codes: list,
            expected_error_code_with_message: dict,
            default_error_message=None
    ):
        if default_error_message is None:
            default_error_message = f'unexpected error {response_code} {response_message}'
        if response_code[0] == '5':
            for i in expected_error_code_with_message:
                if response_code == i:
                    print_log("PROGRAM", b"Your login is " + bytes(f'Error: {expected_error_code_with_message[i]}', 'utf-8'))
                    self.close()
            print_log("PROGRAM", b"Your login is " + bytes(f'Error: {default_error_message}', 'utf-8'))
            self.close()
        else:
            if response_code not in expected_success_codes:
                print_log("PROGRAM", b"Your login is " + bytes(f'{self.to}  Warning: unexpected success response code: {response_code}', 'utf-8'))

    # def get_all_images(self):
    #     for filename in os.listdir(self.images):
    #         if filename[filename.rfind(".") + 1:] in self.image_dict:
    #             yield filename, self.image_dict[filename[filename.rfind(".") + 1:]]

    def run(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(get_addr(self.smtp_server_address))
            m = self.sock.recv(1024)
            if self.show_verbose:
                print_log("SERVER", m)
        except OSError:
            self.throw_error('invalid smtp server or port')
        except ValueError:
            self.throw_error('invalid smtp server or port')

        self.hello()
        if self.use_ssl:
            self.start_tls()

        if self.use_auth:
            self.auth()
        self.mail()
        self.rcpt()
        self.data()
        self.quit()
        self.close()

    def send(self, text, recv=True, need_print=True):
        if self.show_verbose and need_print:
            print_log("CLIENT", text)
        self.sock.sendall(text)
        if recv:
            t = self.sock.recv(1024)
            if self.show_verbose and need_print:
                print_log("SERVER", t)

            r = list()
            for i in list(filter(None, t.decode('utf-8').split('\r\n'))):
                r.append((i[:3], i[4:]))
            return r

        return [(000, 'server response was not read')]

    def hello(self):
        codes = self.send(b'EHLO ' + bytes(get_addr(self.smtp_server_address)[0], 'utf-8') + b'\r\n')

        for i in codes:
            self.check_response_code_for_errors(i[0], i[1], ['250'], {}, 'error after command "EHLO"')
            if i[0] == '250':
                if 'STARTTLS' in i[1].split(' '):
                    self.ssl_available = True
                if 'AUTH' in i[1].split(' '):
                    self.auth_available = True

    def start_tls(self):
        if not self.ssl_available:
            self.throw_error('ssl is not available in this smtp server')

        code = self.send(b"STARTTLS\r\n")
        self.check_response_code_for_errors(code[0][0], code[0][1], ['220'], {}, 'STARTTLS error')
        self.sock = ssl.wrap_socket(self.sock)

    def auth(self):
        if not self.auth_available:
            self.throw_error('auth is not available in this smtp server')

        code = self.send(b'AUTH Login\r\n')
        self.check_response_code_for_errors(code[0][0], code[0][1], ['334'], {'530': 'ssl permission required'},)

        code = self.send(base64.b64encode(bytes(self.user, "utf-8")) + b'\r\n')
        self.check_response_code_for_errors(code[0][0], code[0][1], ['334'], {})
        # print_log("PROGRAM", b"Your login is " + bytes(self.user, 'utf-8'))
        p = ''
        try:
            # p = getpass.getpass(prompt='PROGRAM\t\tEnter password:')
            p = ""
        except KeyboardInterrupt:
            self.close()
        code = self.send(base64.b64encode(bytes(p, "utf-8")) + b'\r\n')
        self.check_response_code_for_errors(code[0][0], code[0][1], ['235'], {'535': 'authentication failed: Invalid user or password!'})

    def mail(self):
        code = self.send(bytes(f"MAIL FROM: <{self.user}>\r\n", "utf-8"))
        self.check_response_code_for_errors(code[0][0], code[0][1], ['250'], {'503': 'auth permission required', '530': 'auth permission required'})

    def rcpt(self):
        code = self.send(bytes(f"RCPT TO: <{self.to}>\r\n", 'utf-8'))
        self.check_response_code_for_errors(code[0][0], code[0][1], ['250'], {})

    def data(self):
        code = self.send(b"DATA \r\n")
        self.check_response_code_for_errors(code[0][0], code[0][1], ['354'], {})

        self.send(b"From: <" + bytes(self.user, 'utf-8') + b">\r\n", False)

        self.send(b"Subject: " + bytes(self.subject, 'utf-8') + b"\r\n", False)
        self.send(b"\r\n", False)

        file = open(self.text_file, "r", encoding='utf-8')

        for line in file.readlines():
            # print("начал")
            # if line[-1] == "\n":
            #     line = line[:-1]
            self.send(bytes(f"{line}", 'utf-8'), False, True)
            # print("закончил")
            # self.send(b"\r\n")

        file.close()
        # for image in self.get_all_images():
        #     self.send(b"\r\n", False)
        #     self.send(b"--qwerty\r\n", False)
        #     self.send(bytes(f"Content-Type: image/{image[1]}; name={image[0]}\r\n", 'utf-8'), False)
        #     self.send(bytes(f"Content-Transfer-Encoding: base64\r\n", 'utf-8'), False)
        #     self.send(bytes(f"Content-Description: {image[0]}\r\n", 'utf-8'), False)
        #     self.send(bytes(f'Content-Disposition:attachment;filename:"{image[0]}"; {os.path.getsize(os.path.join(self.images, image[0]))}\r\n', 'utf-8'), False)
        #     with(open(os.path.join(self.images, image[0]), 'rb')) as image_f:
        #         image_64_encode = base64.b64encode(image_f.read())
        #     self.send(b"\r\n", False)
        #     self.send(image_64_encode, False, False)
        #     self.send(b'{image_64_encode}\r\n', False, False)

        # self.send(b"--qwerty--\r\n", False)
        code = self.send(b"\r\n.\r\n")
        self.check_response_code_for_errors(code[0][0], code[0][1], ['251'], {})

    def quit(self):
        code = self.send(bytes("QUIT \r\n", "utf-8"))
        self.check_response_code_for_errors(code[0][0], code[0][1], ['221'], {})
        # print_log("PROGRAM", b"the letter was queued successfully")
        self.close()

    def close(self):
        self.sock.close()

