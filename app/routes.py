from flask import render_template, flash, redirect, url_for, request, send_file
from app import app, ALLOWED_PATTERN_EXTENSIONS, ALLOWED_IMG_EXTENSIONS, globalMap, globalDict
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Pattern, Tag, Comment
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import db
import os.path
import html
import datetime
from io import BytesIO
import calendar
import time

pattsPerRow = 3

#https://www.youtube.com/watch?v=TLgVEBuQURA (file downloading)
#https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world (Flask tutorial)


#Takes a list and creates a list of lists, each with up to 3 elements
def groupInThrees(listy):
    numGroups = -(-len(listy) // pattsPerRow)
    dictInThrees = {k: [] for k in range(numGroups)}#dict.fromkeys(range(numGroups), []) 
    print("dictInThrees:",dictInThrees)
    pattsInThrees = [[] for i in range(numGroups)]
    for i in range(numGroups):
        for j in range(pattsPerRow):
            if ((pattsPerRow*(i) + (j)) < len(listy)):
                pattsInThrees[i].append(listy[pattsPerRow*(i) + (j)])
                dictInThrees[i].append(listy[pattsPerRow*(i) + (j)])
                print("after dictInThrees[",i,"].append, dictInThrees is:",dictInThrees)
                print("and dictInThrees[",i,"] is:",dictInThrees[i])
    print("dictInThrees:",dictInThrees)
    return dictInThrees

#Filters input through permitted file extensions
def allowed_pattern(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_PATTERN_EXTENSIONS

def allowed_img(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXTENSIONS

#Store any tags not in database
def storeTags(tags):
    for tag in tags:
        if Tag.query.filter_by(label=tag).first() is None:
            db.session.add(Tag(label=tag))
    db.session.commit()

def tagLabelsFromObjects(listy):
    tags = []
    for tag in listy:
        tags.append(tag.label)
    return tags

#Routes***************************************************************************
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

#Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

#Profile display route - takes username and displays profile
@app.route('/profile/<userId>', methods=['GET','POST'])
def profile(userId):
    user =  User.query.get(userId)
    if user == None:
        return redirect(url_for('profileForm'))
    comments = Comment.query.filter_by(user_id=userId).all()
    patterns = User.query.filter_by(id=userId).first().uploaded_patterns

    saved = []
    dictionary = {}
    if (current_user.is_authenticated):
        saved = user.saved_patterns

        for p in patterns:
            if p in saved:
                dictionary[p.id] = "s"
            else:
                dictionary[p.id] = "n"

    return render_template('profile.html', title=user.username+"'s Profile", savedDict=dictionary, comments=comments, patterns=groupInThrees(patterns), user=user)

#Displays profile search form
@app.route('/profileForm')
def profileForm():
    return render_template('profileForm.html', title='Search Profiles', err=False)

#Interprets form entries from profileForm and redirects
@app.route('/profileSearch', methods=['GET','POST'])
def profileSearch():
    f = request.form
    username = request.form['username']

    user = User.query.filter_by(username=username).first()
    if user == None:
        return render_template('profileForm.html', title='Search Profiles', err=True)
    else:
        return redirect('/profile/'+str(user.id))

#Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

#Logout route
@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('login'))
    

#Resources page route (returns calendar)
@app.route('/resources')
def resources():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('resources.html', title='Resources')

#Renders upload form
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('upload.html', title='Upload Pattern', edit=False, globalDict = globalDict, globalMap=globalMap)

#Receives upload form data
@app.route('/uploadForm', methods=['GET', 'POST'])
def uploadForm():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    file = request.files['file']
    image = request.files['image']
    name = html.unescape(request.form['name'])
    description = html.unescape(request.form['description'])
    filename = secure_filename(file.filename)
    imagename = secure_filename(image.filename)

    #Create list of tags from form response, store in database if not yet there
    tags = []
    formVals = request.form
    for key in formVals.keys():
        if key in globalDict:
            tags.append(key)
    storeTags(tags)

    #If filename is good, upload new pattern to database
    if allowed_pattern(filename):
        uploadToDB = Pattern(file=file.read(), filename=filename, owner=current_user)
        file.save(os.path.join(app.config['PATTERN_UPLOAD_FOLDER'], filename))

        if ('name' in request.files):
            uploadToDB.name = name
        else:
            array = file.filename.split('.')
            uploadToDB.name = array[0]

        if ('description' in request.files):
            uploadToDB.description = description

        #Upload cover image (if attached) to filesystem
        if (('image' in request.files) and allowed_img(imagename)):
            array = imagename.split('.')
            ts = calendar.timegm(time.gmtime())
            newFilename = str(Pattern.query.filter_by(filename=filename).first().id) + "." + array[1] + "?" + str(ts)
            pathToImage = os.path.join(app.config['UPLOAD_FOLDER'], newFilename)
            if (os.path.exists(pathToImage)):
                os.unlink(pathToImage)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], newFilename))
            uploadToDB.image_filename = newFilename
        # else:
        #     uploadToDB.image_filename = ""

        for tag in tags:
            t = Tag.query.filter_by(label=tag).first()
            uploadToDB.tags.append(t)

        #put new pattern in database
        db.session.add(uploadToDB)
        db.session.commit()

    return redirect(url_for('patterns'))

#Displays patterns - modular, depending on current pattern view
@app.route('/patterns', methods=['GET', 'POST'])
def patterns():
    patts = db.session.query(Pattern)
    allPatts = patts.all()
    patternIntersection = allPatts
        
    return render_template('patterns.html', title='Patterns', patterns=groupInThrees(patternIntersection), \
        globalDict=globalDict, globalMap=globalMap, saved=False)

@app.route('/viewPattern/<pattId>', methods=['GET','POST'])
def viewPattern(pattId):
    p = Pattern.query.get(pattId)
    if p is None:
        return redirect(url_for('patterns'))
        
    return render_template('viewPattern.html', title=p.name, p=p)
    

#Renders patterns.html with patterns in library
@app.route('/savedPatterns', methods=['GET', 'POST'])
def savedPatterns():
    if not current_user.is_authenticated:
        redirect(url_for('patterns'))

    #Get list of saved patterns:
    saved = []
    if (current_user.is_authenticated):
        saved = User.query.filter_by(id=current_user.id).first().saved_patterns

    return render_template('patterns.html', title='Patterns', patterns=groupInThrees(saved), \
        globalDict=globalDict, globalMap=globalMap, saved=True)

#Renders patterns.html with appropriate filters
@app.route('/filter/<save>', methods=['GET', 'POST'])
def filter(save):
    tagsList = []
    checkedTags = request.form
    for key in checkedTags.keys():
        tagsList.append(key)
        if Tag.query.filter_by(label=key).first() is None:
            db.session.add(Tag(label=key))
    db.session.commit()

    q = db.session.query(Pattern)
    allPatts = q.all()
    if (save == 's'):
        q = q.filter(Pattern.users.any(User.username == current_user.username))

    for tag in tagsList:
        q = q.filter(Pattern.tags.any(Tag.label == tag))

    viewedPatts = q.all()
    filtered = True
    if(len(tagsList) == 0):
        filtered = False

    if (save == 'n'):
        onSaved = False
    else:
        onSaved = True

    return render_template('patterns.html', title='Patterns', patterns=groupInThrees(viewedPatts), \
        globalDict=globalDict, filtered=filtered, tags=tagsList, globalMap=globalMap, saved=onSaved)

#Receives signal from edit button and renders edit form
@app.route('/edit/<pattId>', methods=['GET', 'POST'])
def edit(pattId):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    p = Pattern.query.get(pattId)
    if not (current_user.id == p.user_id or current_user.username == "admin"):
        return redirect(url_for('patterns'))

    tags = tagLabelsFromObjects(p.tags)
    
    return render_template('upload.html', title='Edit Pattern', globalDict=globalDict, edit=True, p=p, tags=tags, globalMap=globalMap)

#Receives data from edit form, updates DB, and redirects to patterns
@app.route('/editForm/<pattId>', methods=['GET', 'POST'])
def editForm(pattId):
    print ('entered editForm route')
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    p = Pattern.query.get(pattId)
    if not (current_user.id == p.user_id or current_user.username == "admin"):
        return redirect(url_for('patterns'))

    image = request.files['image']
    imagename = secure_filename(image.filename)

    if (('image' in request.files) and allowed_img(imagename)):
        pathToImage = os.path.join(app.config['UPLOAD_FOLDER'], p.image_filename)
        if (os.path.exists(pathToImage)):
            os.unlink(pathToImage)

        ts = calendar.timegm(time.gmtime())
        array = imagename.split('.')
        newFilename = str(pattId) + "." + array[1] + "?" + str(ts)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], newFilename))
        p.image_filename = newFilename
    
    f = request.form
    tags = []
    for key in f.keys():
        if key == 'name':
            if (f[key] is not "") and (f[key] is not None):
                p.name = f[key]
            else:
                array = p.filename.split('.')
                p.name = array[0]
        elif key == 'description':
            p.description = f[key]
        else:
            tags.append(f[key])

        storeTags(tags)
        p.tags = []
        for t in tags:
            p.tags.append(Tag.query.filter_by(label=t).first())

    db.session.commit()
    return redirect(url_for('patterns'))

#Receives signal from delete button, deletes pattern from DB, and redirects to patterns route
@app.route('/delete/<pattId>', methods = ['GET', 'POST'])
def delete(pattId):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    p = Pattern.query.get(pattId)
    if not (current_user.id == p.user_id or current_user.username == "admin"):
        return redirect(url_for('patterns'))

    comments = Comment.query.filter_by(pattern_id=pattId).all()
    for c in comments:
        db.session.delete(c)
    
    if not (p.image_filename == None or p.image_filename == ""):
        pathToImage = os.path.join(app.config['UPLOAD_FOLDER'], p.image_filename)
        if (os.path.exists(pathToImage)):
            os.unlink(pathToImage)

    pathToFile = os.path.join(app.config['PATTERN_UPLOAD_FOLDER'], p.filename)
    if (os.path.exists(pathToFile)):
        os.unlink(pathToFile)

    db.session.delete(p)
    db.session.commit()
    return redirect(url_for('patterns'))

#Adds requested pattern to library and reloads patterns route
@app.route('/add/<pattId>', methods=['GET', 'POST'])
def add(pattId):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    p = Pattern.query.get(pattId)
    user = User.query.get(current_user.id)
    if not p in user.saved_patterns:
        user.saved_patterns.append(p)
        db.session.commit()
    return redirect(url_for('patterns'))

#Removes requested pattern from library and reloads patterns route
@app.route('/remove/<pattId>', methods=['GET', 'POST'])
def remove(pattId):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    p = Pattern.query.get(pattId)
    user = User.query.get(current_user.id)
    if p in user.saved_patterns:
        user.saved_patterns.remove(p)
        db.session.commit()
    return redirect(url_for('patterns'))

#Downloads pattern
@app.route('/download/<pattId>', methods=['GET', 'POST'])
def download(pattId):
    p = Pattern.query.get(pattId)
    return send_file(BytesIO(p.file), attachment_filename = p.filename, as_attachment = True)

#Receives signal from comments button, creates comments list, and renders comments template
@app.route('/comments/<pattId>', methods=['GET', 'POST'])
def comments(pattId):
    if not current_user.is_authenticated:
        return redirect(url_for('patterns'))
    p = Pattern.query.get(pattId)
    # comments = p.comments
    # usersComments = {}
    # i = 0
    # for c in comments:
    #     name = User.query.get(c.user_id).username
    #     usersComments[i] = c
    #     i = i + 1
    return render_template('comments.html', title="Pattern Info", p=p)#, comments=p.comments)

#Detects comment submission, adds to database, and redirects to comments of current pattern
@app.route('/commentUpload/<pattId>', methods=['GET', 'POST'])
def commentUpload(pattId):
    if not current_user.is_authenticated:
        return redirect(url_for('patterns'))
    body = request.form['body']
    p = Pattern.query.get(pattId)
    # u = User.query.get(current_user.id)
    c = Comment(body=body)
    p.comments.append(c)
    current_user.comments.append(c)
    db.session.add(c)
    db.session.commit()
    return redirect('/comments/'+str(pattId))

#Detects comment's delete submission, removes from DB, and redirects to comments of current pattern
@app.route('/commentDelete/<commentId>', methods=['GET', 'POST'])
def commentDelete(commentId):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    c = Comment.query.get(commentId)
    if not (current_user.id == c.author or current_user.username == "admin"):
        return redirect(url_for('patterns'))
    
    pattId = c.pattern_id
    db.session.delete(c)
    db.session.commit()
    return redirect('/comments/'+str(pattId))

@app.route('/manage')
def manage():
    if not (current_user.is_authenticated and current_user.username == "admin"):
        return redirect(url_for('index'))

    patterns = Pattern.query.all()
    users = User.query.all()

    return render_template('manage.html', title="Manage", patterns=patterns, users=users)


#Routes for knitting/crochet tutorials
@app.route('/castOn')
def castOn():
    return render_template('castOn.html', title='Casting On')

@app.route('/knitPurl')
def knitPurl():
    return render_template('knitPurl.html', title='Knit Stitch')

@app.route('/chain')
def chain():
    return render_template('chain.html', title='Chaining')

@app.route('/singleDouble')
def singleDouble():
    return render_template('singleDouble.html', title='Single Crochet')
