from wtforms import TextField, PasswordField, SubmitField, BooleanField, validators, ValidationError
from sqlalchemy import or_
from flask.ext.wtf import Form
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import User
import pdb
