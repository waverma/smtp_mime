import argparse
import os

from smtp_client import SMTPClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssl", action='store_true', help="разрешить использование ssl, если сервер поддерживает (по умолчанию не использовать)")
    parser.add_argument("-s", "--server", type=str, required=True, help="адрес (или доменное имя) SMTP-сервера в формате адрес[:порт] (порт по умолчанию 25)")
    parser.add_argument("-t", "--to", type=str, required=True, help="почтовый адрес получателя письма")
    parser.add_argument("-f", "--from", type=str, dest="user", default="<>", help="почтовый адрес отправителя (по умолчанию <>)")
    parser.add_argument("--subject", type=str, default="Happy Pictures", help="необязательный параметр, задающий тему письма, по умолчанию тема “Happy Pictures”")
    parser.add_argument("--auth", action='store_true', help="запрашивать ли авторизацию (по умолчанию нет), если запрашивать, то сделать это после запуска, без отображения пароля")
    parser.add_argument("-v", "--verbose", action='store_true', help="отображение протокола работы (команды и ответы на них), за исключением текста письма")
    parser.add_argument("-d", "--directory", type=str, default=os.getcwd(), help="каталог с изображениями (по умолчанию $pwd)")
    args = parser.parse_args()
    SMTPClient(args.user, args.to, args.subject, args.directory, args.ssl, args.server, args.auth, args.verbose).run()
