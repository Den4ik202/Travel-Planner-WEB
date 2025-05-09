import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class Route(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'routs'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    distance = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    coordinate_places =  sqlalchemy.Column(sqlalchemy.String, nullable=True)
    full_adress_places =  sqlalchemy.Column(sqlalchemy.String, nullable=True)
    enicoding_image = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    
    user_id = sqlalchemy.Column(sqlalchemy.Integer, 
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')
