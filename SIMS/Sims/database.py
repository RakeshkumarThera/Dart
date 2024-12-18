# author: Saif ali Karedia

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

Base = declarative_base()
session = None
metadata = None
Session = None


def init_db(uri):
    global session
    global metadata
    global Session
    engine = create_engine(uri)
    metadata = MetaData(engine)
    Session = sessionmaker(bind=engine)
    session = Session()  # use this session object

    # include all the models here
    from project.models.user import User
    from project.models.node import Node
    from project.models.cluster import Cluster
    from project.models.type import Type
    from project.models.audit_cluster import AuditCluster

    Base.metadata.create_all(bind=engine)  # create the table from the models if it is first time
