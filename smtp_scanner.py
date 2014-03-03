import socket
import ssl


DEBUG = True

SMTP_IDENT = "UCSD-222"
certs_file = "cacert.pem"

SSL23 = 0
SSL3 = 1
TLS1 = 2

num_ssl_types = 3

class smtp_server:
    '''a struct to hold data from a smtp scan'''
    ip = None

    '''variable to track is ESMTP is being used'''
    esmtp = None
    esmtp_resp = list()

    '''TLS support information'''
    tls = None
    starttls = None

    '''ssl connection information'''
    ssl_cipher_name = [None] * num_ssl_types
    ssl_cipher_version = [None] * num_ssl_types
    ssl_cipher_bits = [None] * num_ssl_types
    ssl_verified = [None] * num_ssl_types
    ssl_cert = [None] * num_ssl_types


    def __init__(self,ip):
        '''constructor, pass the ip of the sever quering'''
        self.ip = ip

    def __repr__(self):
        '''return the result as a printable string'''
        return "[%s]\n\tESMTP: %s\n\tTLS: %s\n\tSSL: [%s:%s:%s]" %\
                        (self.ip, str(self.esmtp), str(self.tls),
                        str(self.ssl_cipher_name), str(self.ssl_cipher_version),
                        str(self.ssl_cipher_bits))


class smtp_scanner:
    '''class to hold all methods related to scanning and querying
    smtp servers'''

    def queryServer(self, ip):
        '''queries a server and returns the results of the server
        in question'''
    
        server_result = smtp_server(ip)

        '''run tls checks'''
        self.run_test(SSL23, server_result)
        self.run_test(SSL3, server_result)
        self.run_test(TLS1, server_result)

        return server_result

    def run_test(self, version, server_result, timeout=5):
        '''runs and saves all tests for the provided ssl version'''
        conn = self.connect(server_result.ip, 25, timeout)
        if not conn:
            if DEBUG:
                print "unable to connect to server: "+server_result.ip
            return

        ''' if helo failed skip this port'''
        if not self.ehlo_helo(conn, server_result):
            if DEBUG:
                print "helo failed"
            return

        '''run tls check'''
        self.trytls(conn, version, server_result)

        conn.close()


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

    def ehlo_helo(self, conn, server_result):
        '''runs both helo and ehlo on the server to determine if ESMTP is suppported
        also sets the methods supported via the ehlo response'''

        '''try EHLO first, if fails fall back to HELO'''
        ehloCommand = 'EHLO '+SMTP_IDENT+'\r\n'
        conn.send(ehloCommand)
        recv = conn.recv(1024)
        if recv[:3] != '250':
            server_result.esmtp = False

            '''attempt again with HELO'''
            ehloCommand = 'HELO '+SMTP_IDENT+'\r\n'
            conn.send(heloCommand)
            if recv[:3] != '250':
                '''something went very wrong'''
                if DEBUG:
                    print "no helo reponse: "+server_result.ip
                return False
            else:
                return True
        else:
            server_result.esmtp = True
            '''check to see if the server claims tls support'''
            server_result.starttls = False
            for line in recv:
                if line[4:12].upper() == 'STARTTLS':
                    server_result.starttls = True
                    break

        '''the response to the EHLO command is not a sumer important metric beause we have found that
        it is not a good indecator of weeather starttls is supported'''
        ''' add response to data '''
        for line in recv.splitlines()[1:]:
            if line[:3] == '250':
                server_result.esmtp_resp.append(line[4:])

        return True

    def trytls(self, conn, version, server_result):
        '''send the server the starttls command to see if it is supported'''

        ssl_protocol = None
        if version == TLS1:
            ssl_protocol = ssl.PROTOCOL_TLSv1
        elif version == SSL23:
            ssl_protocol = ssl.PROTOCOL_SSLv23
        elif version == SSL3:
            ssl_protocol = ssl.PROTOCOL_SSLv3
        else:
            print "BAD ssl version: "+str(version)
            return False
        
        tlsCommand = 'STARTTLS\r\n'
        conn.send(tlsCommand)
        recv = conn.recv(1024)

        if recv[:3] != '220':
            if server_result.tls != True:
                server_result.tls = False
            return False

        '''start ssl connection'''
        ssl_conn = None
        try:
            ssl_conn = ssl.wrap_socket(conn, ssl_version=ssl_protocol, cert_reqs=ssl.CERT_OPTIONAL, ca_certs=certs_file)
        except ssl.SSLError as err:
            if err.args[0] == 1: #verify error
                server_result.ssl_verified[version] = False #TODO this is never set to true 
                print "SSL exception!"
                #TODO reconnect withour key verification
                #a better way would be to get the binary key from the server and verify it locally
                #ssl_conn = ssl.wrap_socket(conn, ssl_version=ssl.PROTOCOL_SSLv23, cert_reqs=ssl.CERT_OPTIONAL, ca_certs="cacert.pem")
            else:
                server_result.tls = False
                return False
        
        if ssl_conn != None:
            server_result.tls = True

            '''save all ssl information'''
            cipher = ssl_conn.cipher()
            server_result.ssl_cipher_name[version] = cipher[0]
            server_result.ssl_cipher_version[version] = cipher[1]
            server_result.ssl_cipher_bits[version] = cipher[2]

            cert = ssl_conn.getpeercert()
            if len(cert) > 0:
                server_result.ssl_cert[version] = cert


if __name__ == "__main__":
    scanner = smtp_scanner()

    iplist = ['aspmx.l.google.com', 'hackers.ucsd.edu', 'inbound.ucsd.edu', 'mx-v.av-mx.com']

    for ip in iplist:
        print "trying: "+ip
        print scanner.queryServer(ip)
        print "====================="


