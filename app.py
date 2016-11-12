######################################
#Han Xiao xh1994@bu.edu U11740340
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################




#Han Xiao xh1994@bu.edu U11740340

import flask
from flask import Flask, Response, request, render_template, redirect, url_for

from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import time

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'XHbilly@680628'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	try:
		user.is_authenticated = request.form['password'] == pwd 
		return user
	except:
		pass

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		fname=request.form.get('fname')
		lname=request.form.get('lname')
		bday=request.form.get('bday')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
	except:
		print ("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print (cursor.execute("INSERT INTO Users (email, password,fname,lname,bday,hometown,gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password,fname,lname,bday,hometown,gender)))
		conn.commit()
		#log user in
		user = User()
		#USER ID IN FLASK IS USER EMAIL IN DATABASE!!!!!!!!!!!!!!
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print ("couldn't find all tokens")
		return render_template('register.html')
		#print render_template('register.html', supress = True)
		#this doesnt show the error message, I tried render_template but it leads to an 
		#attribute error, I have no idea why this happens! I saw on piazza there are two
		#questions with the same problem, no one fixed it or answered it correctly ! I think
		#there should be a instructor answer for this problem......I search lots of ways to fix this
		#but didnt work....SO i am thinking it might be a problem with template or my computer is lack of something...
		#return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption FROM album_contain_photo WHERE photo_owner_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserEmailFromId(id):
	cursor = conn.cursor()
	cursor.execute("SELECT email  FROM Users WHERE user_id = '{0}'".format(id))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def getallphotos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata,photo_id,caption,contain_album_id FROM album_contain_photo")
	return cursor.fetchall()
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos = getallphotos())

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		contain_album_id = request.form.get('contain_album_id')
		print (caption)
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		if cursor.execute("SELECT owner_id from Album where owner_id = '{0}' and album_id = '{1}'".format(uid,contain_album_id)):
			#cursor = conn.cursor()
			cursor.execute("INSERT INTO album_contain_photo (photo_owner_id, imgdata, contain_album_id, caption) VALUES ('{0}', '{1}', '{2}', '{3}' )".format(uid, photo_data, contain_album_id, caption))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getallphotos())
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message='Photo upload failed because the album id you entered is not yours!', photos=getallphotos())
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code 


#delete album
@app.route('/delete_album/<album_id>', methods=['GET','POST'])
@flask_login.login_required
def delete_album(album_id):
	if request.method=='POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		delete_message = request.form.get('description')
		cursor = conn.cursor()
		if delete_message == "Yes" and cursor.execute("SELECT album_id from Album where owner_id = '{0}'".format(uid)):
			print delete_message
			cursor.execute("DELETE from Album Where album_id = '{0}'".format(album_id))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='album deleted!', photos=getallphotos())
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message='album deletion failed because the photo is not yours or enter the message that is not Yes!', photos=getallphotos())
	else:
		return render_template('delete_album.html', album_id = album_id)



#delete photo
@app.route('/delete/<photo_id>', methods=['GET','POST'])
@flask_login.login_required
def delete(photo_id):
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		#imgfile = request.files['photo']
		#caption = request.form.get('caption')
		#contain_album_id = request.form.get('contain_album_id')
		#print (caption)
		#photo_data = base64.standard_b64encode(imgfile.read())
		delete_message = request.form.get('description')
		cursor = conn.cursor()
		if delete_message == "Yes" and cursor.execute("SELECT photo_id from album_contain_photo where photo_owner_id = '{0}'".format(uid)):
			#cursor = conn.cursor()
			print delete_message
			cursor.execute("DELETE from album_contain_photo Where photo_id = '{0}'".format(photo_id))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Photo deleted!', photos=getallphotos())
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message='Photo deletion failed because the photo is not yours or enter the message that is not Yes!', photos=getallphotos())
	else:
		return render_template('delete.html', photo_id = photo_id)


@app.route('/showyourphoto', methods=['GET'])
@flask_login.login_required
def showyourphoto():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message='Here are your photos!', photos=getUsersPhotos(uid))


#helper functin to list all friends of a user id
def listfriend(email):
	cursor = conn.cursor()
	cursor.execute("SELECT friend_email FROM user_have_friends WHERE user_email = '{0}'".format(email))
	return cursor.fetchall()

@app.route('/listfriends', methods = ['GET'])
@flask_login.login_required
def userlistfriends():
	return render_template('listfriends.html',name=flask_login.current_user.id, friends = listfriend(flask_login.current_user.id))

#adding friends 

@app.route('/addfriend', methods = ['GET','POST'])
@flask_login.login_required
def add_friend():
	if request.method == 'POST':
		#user_email = getUserEmailFromId(flask_login.current_user.id)
		friend_email = request.form.get('email')
		cursor = conn.cursor()
		if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(friend_email)):
			cursor.execute("INSERT INTO user_have_friends(user_email,friend_email) VALUES('{0}', '{1}')".format(flask_login.current_user.id,friend_email))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message ='friend added!')
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message ='friend adding failed because email entered does not exist!')
	else:
		return render_template('addfriend.html', name = flask_login.current_user.id)



#check if albumname is unique for the user registered 
def albumname_unique_within_oneuser(owner_id):
	cursor = conn.cursor()
	cursor.execute("SELECT album_name FROM Album WHERE owner_id ='{0}'".format(owner_id))
	lists = [item[0] for item in cursor.fetchall()]
	return lists

@app.route('/createalbum', methods = ['GET','POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		album_name = request.form.get('album_name')
		userid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		if album_name not in albumname_unique_within_oneuser(userid):#cursor.execute("SELECT album_name FROM Album WHERE owner_id = '{0}' AND album_name ='{1}'".format(userid,album_name)):
			cursor.execute("INSERT INTO Album(album_name,owner_id, date_of_creation) VALUES('{0}', '{1}', '{2}')".format(album_name,userid,time.strftime("%Y/%m/%d")))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message ='Album created!')
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message ='Album creation failed becasue this name already existed in your album list')
	else:
		return render_template('createalbum.html', name = flask_login.current_user.id)


def listalbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_name,album_id,date_of_creation FROM Album WHERE owner_id = '{0}'".format(uid))
	return cursor.fetchall()

def list_all_albums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_name,album_id FROM Album")
	return cursor.fetchall()

@app.route('/listalbums', methods = ['GET'])
@flask_login.login_required
def list_albums():
	if request.method == 'GET':
		return render_template('listalbums.html',name=flask_login.current_user.id, albums = listalbums(getUserIdFromEmail(flask_login.current_user.id)))

#maximum recursion depth exceeded??????????
@app.route('/listallalbums', methods = ['GET'])
def listallalbums():
	if request.method == 'GET':
		return render_template('listallalbums.html', albums = list_all_albums())
	#if request.method == 'GET':
		#return render_template('listallalbums.html',name="visitor", albums = listallalbums())

def getphotoinalbum(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id, imgdata, caption FROM album_contain_photo WHERE contain_album_id = '{0}'".format(album_id))
	return cursor.fetchall()

#to show photos in an album
#not work, nonetype error????
@app.route('/album/<album_id>', methods = ['GET'])
@flask_login.login_required
def photo_in_album(album_id):
	print album_id
	if request.method == 'GET':
		photo = getphotoinalbum(album_id)
		return render_template('showphotoinalbum.html', name = flask_login.current_user.id, album_id = album_id, photos = photo)


#helper for top 10 users
def top10userdata():
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(photo_id)+COUNT(comment_id) AS popular, email FROM photo_have_comments, Users, album_contain_photo WHERE user_id = comment_owner_id and user_id = photo_owner_id and photo_owner_id = comment_owner_id GROUP BY user_id order by popular DESC LIMIT 10")
	return cursor.fetchall()


@app.route('/top10user', methods = ['GET'])
def top10user():
	if request.method == 'GET':
		return render_template('top10user.html', users = top10userdata())


#leaving comments for each photo
@app.route('/comment/<photo_id>', methods = ['GET', 'POST'])
def comment(photo_id):#how to get photoid for comment?
	print photo_id
	if request.method == 'POST':
		#email = getUserIdFromEmail(flask_login.current_user.id)
		comment_text = request.form.get('description')#datatype for text??????
		comment_date = time.strftime("%Y/%m/%d")
		cursor = conn.cursor()
		uid = getUserIdFromEmail(flask_login.current_user.id)
		if cursor.execute("SELECT photo_id from album_contain_photo, photo_have_comments WHERE comment_photoid = photo_id and photo_owner_id='{0}'".format(uid)):
			return render_template('hello.html', name=flask_login.current_user.id, message='Comment failed because the photo is yours!', photos=getallphotos())
		else:
			cursor.execute("INSERT INTO photo_have_comments (comment_owner_id,comment_text, comment_date, comment_photoid) VALUES ('{0}', '{1}', '{2}','{3}')".format(uid,comment_text,comment_date,photo_id))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Comment uploaded!', photos=getallphotos() )
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('comment.html', photoid = photo_id)

#get comments for one photo
def getcomments(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT comment_id, comment_owner_id, comment_text, comment_date FROM photo_have_comments WHERE comment_photoid = '{0}'".format(photo_id))
	return cursor.fetchall()

#show all the comments of a photo
@app.route('/showcomment/<photo_id>', methods = ['GET'])
def showcomments(photo_id):
	print getcomments(photo_id)
	return render_template('showcomment.html', comments  = getcomments(photo_id))


#check if the entered tag exists already
def TagExist(new_tag,photo_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT * from tag_and_photo WHERE tag_word='{0}' and photoid_intag ='{1}'".format(new_tag,photo_id)):
		return True
	else:
		return False


#create tag
# and like a photo!!!!!!!!!!!!!!!!!!!!
@app.route('/tag/<photo_id>', methods = ['GET', 'POST'])
def tag(photo_id):
	if request.method == 'POST':
		#email = getUserIdFromEmail(flask_login.current_user.id)
		tag_text = request.form.get('description')#datatype for text??????
		if (TagExist(tag_text,photo_id)) == False:
			cursor = conn.cursor()
			cursor.execute("INSERT INTO tag_and_photo (tag_word,photoid_intag) VALUES ('{0}', '{1}')".format(tag_text,photo_id))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Tag added!', photos=getallphotos())
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message='Tag already exists!', photos=getallphotos())
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('tag.html', photoid = photo_id)

#get tags for one photo
def gettags(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_word FROM tag_and_photo WHERE photoid_intag = '{0}'".format(photo_id))
	return cursor.fetchall()

#get photos for tags, one or more tags for tag search
def getphotointag(tag_word):
	if isinstance(tag_word,str):
		taglist = tag_word.split()
	else:
		taglist = tag_word
	cursor = conn.cursor()
	photoidlistrepeat=[]
	result1=[]
	result=[]
	#get all photo id that has the tags in taglists, can have dupicates
	for i in taglist:
		cursor.execute("SELECT photoid_intag FROM tag_and_photo WHERE tag_word='{0}'".format(i))
		for x in cursor.fetchall():
			photoidlistrepeat.append(x[0])
	#d = [x for x in d if d.count(x) == 1]
	#get all dulpicate photoid which means both tags appear in the photo
	#print photoidlistrepeat
	photoidlistrepeat = list(set([a for a in photoidlistrepeat if photoidlistrepeat.count(a) == len(taglist)]))
	#print photoidlistrepeat
	for a in photoidlistrepeat:
		cursor.execute("SELECT imgdata, photo_id FROM album_contain_photo WHERE photo_id = '{0}'".format(a))
		result.append(cursor.fetchall())
	#print result[0][0]
	#for x in cursor:
		#result.append(x[0])
	#return result
	#lists = [item[0] for item in cursor.fetchall()]
	#testlists = [i[1] for i in cursor.fetchall()]
	#print testlists
	if isinstance(tag_word,str):
		for b in result:
			result1.append(b[0])
	#print result1
		return result1
	else:
		for b in result:
			result1.append(b[0])
		#print result1
		return result1


#get photos for a particular tag for show photo in tag
def getphotoinonetag(tag_word):
	cursor = conn.cursor()
	#result = []
	cursor.execute("SELECT imgdata,photo_id FROM tag_and_photo,album_contain_photo WHERE photo_id = photoid_intag and tag_word = '{0}'".format(tag_word))
	#for x in cursor:
		#result.append(x[0])
	#return result
	return cursor.fetchall()


#show all tags for a particular photo
@app.route('/showtags/<photo_id>', methods = ['GET'])
def showtags(photo_id):
	return render_template('showtags.html', tags = gettags(photo_id))

#show all photos under a tag
@app.route('/photo_of_tag/<tag_word>', methods = ['GET'])
def photo_of_tag(tag_word):
	return render_template('photo_of_tag.html', photos = getphotoinonetag(tag_word))

#helper for parse the tags and get photos contain both tags
'''def getphotoparsetag(tag_word):
	print tag_word
	taglist = tag_word.split()
	print taglist
	photolist = []
	#cursor = conn.cursor()
	for i in taglist:
		print i
		photolist.append(getphotointag(i))
	return photolist'''

#helper test if tags entered exits!!!
def tagsexist(tag_word):
	taglist = tag_word.split(" ")
	exits = 0
	cursor = conn.cursor()
	for i in range(len(taglist)):
		if cursor.execute("SELECT tag_word FROM tag_and_photo WHERE tag_word = '{0}'".format(taglist[i])):
			exits = exits+1
	if exits == len(taglist):
		return True

#search photo by tag
#conjunctive????parser..doesnt work!!!!!!!!!!!!!
@app.route('/photo_search_by_tag', methods = ['POST'])
def photo_search_by_tag():
	if request.method == 'POST':
		#user_email = getUserEmailFromId(flask_login.current_user.id)
		tag_word = request.form.get('tag_word')
		#print tag_word
		#print getphotointag(tag_word)[0][1]
		#cursor = conn.cursor()
		taglist = tag_word.split()
		if tagsexist(tag_word):
			#print getphotoparsetag(tag_word)
			if len(taglist) != 1:
				return render_template('photo_search_by_tag.html', photos = getphotointag(tag_word), tag_word = tag_word)
			else:
				return render_template('photo_search_by_tag.html', photos = getphotoinonetag(tag_word), tag_word = tag_word)
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message ='Search failed because the tag does not exist')

#helper to get 5 most common user tag of a user
def mostcommon5tag(uid):
	cursor = conn.cursor()
	taglist = []
	cursor.execute("SELECT tag_word, count(photoid_intag) from tag_and_photo, album_contain_photo where photo_owner_id='{0}' and photo_id = photoid_intag group by tag_word order by count(photoid_intag) DESC LIMIT 5".format(uid))
	for i in cursor.fetchall():
		taglist.append(i[0])
	return taglist


#photo rank


#photo search by tag list
def tagsearchphoto(taglist):
	print taglist
	photolist = []
	#cursor = conn.cursor()
	for i in taglist:
		print i
		photolist.append(getphotointag(i))
	return photolist




#recommendations you may also like:
@app.route('/youmayalsolike/<name>', methods = ['GET'])
@flask_login.login_required
def youmayalsolike(name):
	taglist = mostcommon5tag(getUserIdFromEmail(flask_login.current_user.id))
	photolist=[]
	taglength = len(taglist)
	for i in range(taglength):
		photolist.append(getphotointag(taglist[i:]))
	#print photolist
	return render_template('hello.html', name = flask_login.current_user.id, photos = photolist[0], message = 'Here are the photo you may also like based on your tags of your photos ranked from the highest relevance top to bottom!')


#return a list of photo ids contain the tags entered
def find_photoid_under_each_tag(tag_word):
	taglist = tag_word.split()
	cursor = conn.cursor()
	photolist=[]
	for i in tag_word:
		cursor.execute("SELECT photoid_intag from tag_and_photo where tag_word ='{0}'".format(i))
		for a in cursor.fetchall():
			photolist.append(a[0])
	return photolist


#return a 2d list with tagword is the first and occurence is the second
def get_tag_occurence(photolist):
	tagoccurence=[]
	taglistrepeat=[]
	taglistdistinct=[]
	cursor = conn.cursor()
	for i in photolist:
		cursor.execute("SELECT tag_word from tag_and_photo where photoid_intag='{0}'".format(i))
		for a in cursor:
			taglistrepeat.append(a[0])
	taglistdistinct=list(set(taglistrepeat))
	for b in range(len(taglistdistinct)):
		tagoccurence.append([taglistdistinct[b],taglistrepeat.count(taglistdistinct[b])])
	tagoccurence.sort(key=lambda x: x[1], reverse = True)
	return tagoccurence



#recommendations tag:
@app.route('/tagrecommendation', methods = ['POST'])
@flask_login.login_required
def tagrecommendation():
	if request.method == 'POST':
		tag_word = request.form.get('recommendation')
		if tagsexist(tag_word):
			photoidlist = find_photoid_under_each_tag(tag_word)
			tag2dlist = get_tag_occurence(photoidlist)
		return render_template('tagrecommendation.html', tags = tag2dlist)



def numberlike(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(like_useremail) from user_like where like_photoid = '{0}'".format(photo_id))
	return cursor.fetchall()

def userslike(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT like_useremail from user_like where like_photoid = '{0}'".format(photo_id))
	return cursor.fetchall()



#like
@app.route('/like/<photo_id>', methods = ['POST','GET'])
@flask_login.login_required
def like(photo_id):
	if request.method == 'POST':
		#email = getUserIdFromEmail(flask_login.current_user.id)
		like_text = request.form.get('description')#datatype for text??????
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		if cursor.execute("SELECT like_useremail from user_like where like_useremail='{0}'".format(uid)) and like_text != "Yes":
			return render_template('hello.html', name=flask_login.current_user.id, message='photo like failed because you typed No or other thingy!', photos=getallphotos())

		elif like_text == "Yes":
			cursor.execute("INSERT INTO user_like (like_useremail,like_photoid) VALUES ('{0}', '{1}')".format(flask_login.current_user.id,photo_id))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='photo liked!', photos=getallphotos())
		
			
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('likephoto.html', photo_id = photo_id, numberlike = numberlike(photo_id), users = userslike(photo_id))

#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare', photos = getallphotos())


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
