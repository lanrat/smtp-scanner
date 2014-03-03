import socket
import ssl


DEBUG = True

SMTP_IDENT = "UCSD-222"
CERT_FILE = "cacert.pem"

class smtp_server:
    '''a struct to hold data from a smtp scan'''
    ip = None

    '''variable to track is ESMTP is being used'''
    esmtp = None
    esmtp_resp = list()

    '''TLS support information'''
    tls = None

    '''ssl connection information'''
    ssl_cipher_name = None
    ssl_cipher_version = None
    ssl_cipher_bits = None
    ssl_verified = None
    ssl_cert = None

    def __init__(self,ip):
        '''constructor, pass the ip of the sever quering'''
        self.ip = ip

    def __repr__(self):
        '''return the result as a printable string'''
        return "[%s]\n\tESMTP: %s\n\tTLS: %s\n\tSSL: [%s:%s:%s]\n\tCert: %s\n\tVerified: %s" %\
                        (self.ip, str(self.esmtp), str(self.tls),
                        str(self.ssl_cipher_name), str(self.ssl_cipher_version),
                        str(self.ssl_cipher_bits), str(self.ssl_cert != None),
                        str(self.ssl_verified))


class smtp_scanner:
    '''class to hold all methods related to scanning and querying
    smtp servers'''
    def __init__(self):
        self.server_result = None
        self.conn = None

    def queryServer(self, ip, ssl_state=ssl.CERT_REQUIRED):
        '''queries a server and returns the results of the server
        in question'''
    
        self.server_result = smtp_server(ip)

        self.conn = self.connect(ip,25)
        if not self.conn:
            if DEBUG:
                print "unable to connect to server: "+ip
            return

        ''' if helo failed skip this port'''
        if not self.ehlo_helo():
            if DEBUG:
                print "helo failed"
            return

        '''run tls check'''
        self.trytls(ssl_state)

        self.conn.close()

        return self.server_result


    def connect(self, ip, port, timeout=5):
        '''attempt to connect to the IP-PORT to establish a connection'''
        smtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        smtpSocket.settimeout(timeout)
        try:
            smtpSocket.connect((ip, port))
            # Read server response
            recv = smtpSocket.recv(1024)
            if recv[:3] != '220':
                if DEBUG:
                    print '220 reply not received from '+ip+':'+str(port)
                return False
            return smtpSocket
        except socket.timeout:
            return False

    def ehlo_helo(self):
        '''runs both helo and ehlo on the server to determine if ESMTP is suppported
        also sets the methods supported via the ehlo response'''

        '''try EHLO first, if fails fall back to HELO'''
        ehloCommand = 'EHLO '+SMTP_IDENT+'\r\n'
        self.conn.send(ehloCommand)
        recv = self.conn.recv(1024)
        if recv[:3] != '250':
            self.server_result.esmtp = False

            '''attempt again with HELO'''
            ehloCommand = 'HELO '+SMTP_IDENT+'\r\n'
            self.conn.send(heloCommand)
            recv = self.conn.recv(1024)
            if recv[:3] != '250':
                '''something went very wrong'''
                if DEBUG:
                    print "no helo reponse: "+self.server_result.ip
                return False
            else:
                return True
        else:
            self.server_result.esmtp = True

        '''the response to the EHLO command is not a sumer important metric beause we have found that
        it is not a good indecator of weeather starttls is supported'''
        ''' add response to data '''
        for line in recv.splitlines()[1:]:
            if line[:3] == '250':
                self.server_result.esmtp_resp.append(line[4:])

        return True

    def trytls(self, ssl_required):
        '''send the server the starttls command to see if it is supported'''
        
        tlsCommand = 'STARTTLS\r\n'
        self.conn.send(tlsCommand)
        recv = self.conn.recv(1024)

        if recv[:3] != '220':
            self.server_result.tls = False
            return False

        '''start ssl connection'''
        ssl_conn = None
        try:
            ssl_conn = ssl.wrap_socket(self.conn, ssl_version=ssl.PROTOCOL_SSLv23, cert_reqs=ssl_required, ca_certs=CERT_FILE)
            self.server_result.ssl_verified = True
        except ssl.SSLError as err:
            if err.args[0] == 1: #verify error
                self.server_result = self.queryServer(self.server_result.ip, ssl.CERT_NONE)
                self.server_result.ssl_verified = False
                return
            else:
                self.server_result.tls = False
                return False
        
        if ssl_conn != None:
            self.server_result.tls = True

            '''save all ssl information'''
            cipher = ssl_conn.cipher()
            self.server_result.ssl_cipher_name = cipher[0]
            self.server_result.ssl_cipher_version = cipher[1]
            self.server_result.ssl_cipher_bits = cipher[2]

            cert = ssl_conn.getpeercert()
            if len(cert) > 0:
                self.server_result.ssl_cert = cert


if __name__ == "__main__":
    scanner = smtp_scanner()

    iplist = ['aspmx.l.google.com', 'hackers.ucsd.edu', 'inbound.ucsd.edu', 'mx-v.av-mx.com']

    for ip in iplist:
        print "trying: "+ip
        print scanner.queryServer(ip)
        print "====================="

