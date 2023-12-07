from aiosmtpd.controller import Controller

class SimpleMailHandler:
    async def handle_DATA(self, server, session, envelope):
        print('Mail from:', envelope.mail_from)
        print('Mail to:', envelope.rcpt_tos)
        print('Mail data:', envelope.content.decode('utf8', errors='replace'))
        return '250 Message accepted for delivery'

if __name__ == '__main__':
    controller = Controller(SimpleMailHandler(), hostname='localhost', port=1025)
    controller.start()

    print('SMTP server running on localhost:1025. Press Ctrl+C to stop.')

    # Wait for the user to stop the server
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    controller.stop()
