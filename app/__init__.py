from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_manager
from flask_bootstrap import Bootstrap
import os

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir,'static/images/')
ALLOWED_PATTERN_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(Config)
db = SQLAlchemy(app)

migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)

#General Globals
globalLabels = {'Craft': ['Knit','Crochet'], \
            'Difficulty': ['Easy','Intermediate','Advanced'], \
            'Item': ['Scarf','Sweater','Hat','Toy','Blanket','Pillow','Other'], 
            'Knitting Techniques': ['Cables','Lace','Double Knitting','Colorwork','Textured'], \
            'Crochet Techniques': ['Single Crochet','Magic Ring']} \

globalDict = {'craft': ['knit','crochet'], \
            'difficulty': ['easy','intermediate','advanced'], \
            'item': ['scarf','sweater','hat','toy','blanket','pillow','other'], 
            'knittingtechniques': ['cables','lace','doubleknitting','colorwork','textured'], \
            'crochettechniques': ['singlecrochet','magicring']} \

globalMap = {}
for i in globalLabels.keys():
    globalMap[i.replace(" ", "").lower()] = i
    for j in globalLabels[i]:
        globalMap[j.replace(" ", "").lower()] = j

from app import routes
