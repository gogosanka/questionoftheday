WTF_CSRF_ENABLED = True
SECRET_KEY = 'itsm0rphintim3'
#UPLOAD_FOLDER = UPLOAD_FOLDER

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}]
    
import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
#SQLALCHEMY_DATABASE_URI = 'mysql://sifusanka:gatewayqotd@sifusanka.mysql.pythonanywhere-services.com'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')