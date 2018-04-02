import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Q8kBexsnBz9k1Fycr'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['peter.senna@gmail.com']

    POSTS_PER_PAGE = 25

    JWT_PASSWORD_TOKEN_EXPIRES = 600
    JWT_PASSWORD_TOKEN_ALGO = 'HS256'
    JWT_INSTALLATION_KEY_EXPIRES = 86400

    EASY_RSA_PATH = '../../vpn/hosts-vpn/'
    EASY_RSA_GEN = './gen-client-conf.py'
    VPN_CLIENT_CONFIG = '/home/peter/dev/iwe/vpn/hosts-vpn/client/client.conf'
    VPN_CA_CRT = '/home/peter/dev/iwe/vpn/hosts-vpn/client/ca.crt'
    VPN_TA_KEY = '/home/peter/dev/iwe/vpn/hosts-vpn/client/ta.key'
