from flask import Flask,flash,render_template,request,redirect,url_for,session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin,login_user, login_required, logout_user, current_user
import os
app = Flask(__name__)
app.secret_key="pelz"
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///blogs.db'


UPLOADS_FOLDER ='static/uploads'
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER


db=SQLAlchemy(app)
bcrypt=Bcrypt(app)
loginmanager = LoginManager(app)
loginmanager.login_view= 'Login'
loginmanager.login_message_category = 'info'

class neww(db.Model, UserMixin):
    id=db.Column(db.Integer(),primary_key=True)
    name=db.Column(db.String(50), nullable=False)
    email=db.Column(db.String(25),unique=True, nullable=False)
    password=db.Column(db.String(200), nullable= False)
    posts= db.relationship("Post",backref='author',lazy=True,cascade='all,delete-orphan')

    def __init__(self,name,email,password,user_id):
        self.name=name
        self.email=email
        self.password=password
        self.user_id=user_id




@loginmanager.user_loader
def load_user(id):
    return neww.query.get(int(id))


class Blogs(db.Model):
   _id=db.Column(db.Integer(),primary_key=True)
   title=db.Column(db.String(100),unique=True)
   content=db.Column(db.String(100),unique=True)
   image=db.Column(db.String(200))

   #Foreign key to Userid
   user_id=db.Column(db.Integer,db.ForeignKey('neww.id'),nullable=False)
   

   def _init_(self,content,title,image):
        self.content=content
        self.title=title
        self.image=image




@app.route('/', methods= ['GET','POST'])
def Register():
   if current_user.is_authenticated:
       return redirect(url_for('blogs'))
   if request.method== 'POST':
       name = request.form['username'].strip()
       email= request.form['useremail'].strip().lower()
       password= request.form['password']
       confirm= request.form['confirm']
       session['name']=name
       session['email']=email
       session['password']=password
       session['confirm']=confirm



       if not name or not email or not password:
           flash('all fields are required', 'danger')
       elif password != confirm:
           flash('passwords do not match', 'danger')
       elif neww.query.filter_by(name=name).first():
           flash('username already taken', 'danger')
       else:
           hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
           print(hashed_pw)
           userdata=neww(name=name,email=email,password=hashed_pw)
           db.session.add(userdata)
           db.session.commit()
           flash('Account created, login!')
           return redirect(url_for('Login'))
   return render_template('register.html')
   

@app.route("/login",methods= ['GET','POST'])
def Login():

    if current_user.is_authenticated:
        return redirect(url_for('blogs'))
    
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        remember= bool(request.form['remember'])

        user = neww.query.filter_by(email=email).first()
        # print(user.password)

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user,remember=remember)
            flash('logged in successfully', 'success')
            return redirect(url_for('blogs'))
        else:
            flash('login failed check email and password')
    return render_template("login.html")





@app.route('/blogs')
@login_required
def blogs():
    total_blogs=Blogs.query.count()
    return render_template('home.html',blogs=Blogs.query.all(), title='blogs page' ,total=total_blogs)


@app.route("/addblog" ,methods=['GET','POST'])
@login_required
def Add_Blog():
   if request.method=='POST':
      title=request.form['title']
      content=request.form['content']
      session['title']=title
      session['content']=content
      file = request.files['image']
    #   file = request.files.get("image")
      print("file:",file)
      print('working!!!!!')

      if file.filename =='':
         return 'No slected file'
      
      if file:
         filepath = os.path.join(app.config['UPLOADS_FOLDER'], file.filename)
         print("filepaath:",filepath)
         file.save(filepath)
      blog_data=Blogs(title=title,content=content,image=file.filename, user_id=current_user.id)
      db.session.add(blog_data)
      db.session.commit()
      
      print("user added successfully...")
   
      return redirect(url_for("blogs"))
   else:
    return render_template("addblog.html")

# to view blog
@app.route('/viewblog/<title>')
@login_required
def viewblog(title):
   print('title:',title)
   blog = Blogs.query.filter_by(title=title).first()
   print('blog:',blog)
   return render_template('view_blog.html',blog=blog)

# to delete from blog
@app.route('/delete/<id>')
def deleteuser(id):
   blog=Blogs.query.get(id)
   if blog:
      db.session.delete(blog)
      db.session.commit()
   return redirect(url_for('blogs')) 

#to edit blog
@app.route("/updateblog/<id>", methods=['GET', 'POST'])
@login_required
def updateblog(id):
    blog = Blogs.query.get(id)

    # check if blog exists
    if not blog:
        return "Blog not found", 404

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        # validate before saving
        if not title or not content:
            error = "Title and content cannot be empty."
            return render_template("updateblog.html", blog=blog, error=error)

        blog.title = title
        blog.content = content

        try:
            db.session.commit()
            print("Blog updated successfully")
            return redirect(url_for('viewblog', title=blog.title))
        except Exception as e:
            db.session.rollback()
            print(f"Error updating blog: {e}")
            error = "Something went wrong. Please try again."
            return render_template("updateblog.html", blog=blog, error=error)

    return render_template("updateblog.html", blog=blog)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have been loooged out', 'info')
    return redirect(url_for('Login'))




with app.app_context():
   db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
