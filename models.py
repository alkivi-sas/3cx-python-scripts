import logging

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Setup SQLAlchemy
Base = automap_base()

logger = logging.getLogger(__name__)


class Users(Base):
    __tablename__ = 'users'


class Extdevice(Base):
    __tablename__ = 'extdevice'


class Codec(Base):
    __tablename__ = 'codec'


class Codec2Gateway(Base):
    __tablename__ = 'codec2gateway'


class Gateway(Base):
    __tablename__ = 'gateway'


class Parameter(Base):
    __tablename__ = 'parameter'


class DnProp(Base):
    __tablename__ = 'dnprop'


class Queue(Base):
    __tablename__ = 'queue'


class IPBXBinder(object):

    def __init__(self, db, dbuser, dbpass, host='localhost', port=5432):
        self.db = db
        self.dbuser = dbuser
        self.dbpass = dbpass
        self.host = host
        self.port = port
        self.create_engine()
        self.prepare()
        self.session = None

    def prepare(self):
        """Create the automap using our class."""
        Base.prepare(self.engine, reflect=True)
        self.Session = sessionmaker(bind=self.engine)

    def create_engine(self):
        """Returns a connection and a metadata object."""
        # We connect with the help of the PostgreSQL URL
        # postgresql://federer:grandestslam@localhost:5432/tennis
        url = 'postgresql://{}:{}@{}:{}/{}'
        url = url.format(self.dbuser,
                         self.dbpass,
                         self.host,
                         self.port,
                         self.db)

        # The return value of create_engine() is our connection object
        self.engine = create_engine(url, client_encoding='utf8')

    def get_session(self):
        """Get a unique session accross calls."""
        if not self.session:
            self.session = self.Session()
        return self.session
