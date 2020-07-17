from flask import render_template, flash, redirect, request, url_for, send_from_directory, abort
import os
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, EditProfileForm, ChangePasswordForm, EmptyForm, PostForm, CommentForm, ReportForm, BanForm, SearchProfileForm, MessageForm
from app.email import send_password_reset_email
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post, Comment, Upvote, Report, Message, Conversation
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse 
from datetime import datetime

from app import fbStorage


@app.before_request
def before_request():
    if current_user.is_authenticated:
        #check banned
        if current_user.banned == 1 and request.path != url_for('logout'):
            return render_template('banned.html', title = 'Banned')
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        messages = current_user.messages_to.union(current_user.messages_from)
        total_flashes = 0
        for message in messages:#even if have boolean, later still need to check thru all msg to see that the boolean false
            if message.flashed == 0 and message.author != current_user:
                total_flashes += 1
                message.flashed = 1
        if total_flashes > 0:
            flash('You have ' + str(total_flashes) + ' new messages!')
        db.session.commit()



@app.route('/', methods = ['GET', 'POST'])
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index', username = current_user.username))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember = form.remember_me.data)
        flash('Logged in successfully')
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.id == 1:
                next_page = url_for('reported_users') ##get dare reports 1st
                                                  ##nav bar to other reports
            else:
                next_page = url_for('index', username = current_user.username)
        return redirect(next_page)
    return render_template('login.html', form = form)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username = form.username.data, email = form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you have successfully registered!')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Registeration', form = form)


@app.route('/index/<username>', methods=['GET', 'POST'])
@login_required
def index(username):
    user = User.query.filter_by(username = username).first()
    if current_user == user or current_user.id == 1:
        #Submit post
        form0 = SearchProfileForm()
        form = EmptyForm()
        form2 = PostForm()
        #Page navigation
        page = request.args.get('page', 1, type=int)
        posts = user.followed_posts().filter_by(banned=0).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('index', username = user.username, page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('index', username = user.username, page=posts.prev_num) \
            if posts.has_prev else None
        return render_template('index.html', title='Home', form=form, form2=form2,
                                posts=posts.items, upvote=Upvote,
                                next_url=next_url, prev_url=prev_url, form0 = form0, fbStorage = fbStorage, user = user)
    else:
        return redirect(url_for('index', username = current_user.username))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/user/<username>') #Profile
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user.banned == 0 or current_user.id == 1: 
        form0 = SearchProfileForm()
        form = EmptyForm() #Follow/Unfollow button
        form2 = BanForm()
        user = user.query.filter_by(username=username).first_or_404()
        page = request.args.get('page', 1, type=int)
        posts = user.own_posts().paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('user', username=user.username, page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('user', username=user.username, page=posts.prev_num) \
            if posts.has_prev else None
        return render_template('user.html', user=user, posts=posts.items, form=form, form2=form2, upvote=Upvote, next_url=next_url, prev_url=prev_url, form0 = form0, fbStorage = fbStorage)
    return render_template('banned.html', title = 'Banned')



@app.route('/upload', methods = ['POST'])
def upload():
    form = PostForm()
    if form.validate_on_submit():
        file = form.dare.data
        post = Post(body=form.post.data, author=current_user)     
        db.session.add(post)
        post = Post.query.order_by(Post.timestamp.desc()).first()
        filename = secure_filename("{}_{}_{}.mp4".format(str(post.author.id), str(post.author.username), str(post.id)))
        '''
        local_path = app.config["UPLOAD_FOLDER"]
        specific_path = local_path + '/' + str(current_user.id) + '_' + current_user.username
        os.chdir(local_path)
        if not os.path.exists(str(current_user.id) + '_' + current_user.username):#directory for each person
            os.mkdir(str(current_user.id) + '_' + current_user.username)
        proper_path = app.config["TOP_LEVEL"]

        file.save(os.path.join(specific_path, filename))

        os.chdir(proper_path)
        '''
        print('upload filename: ' + filename)
        fbStorage.child(filename).put(file)

        post.dare = filename
        db.session.commit()
        flash('Your post is now live!')
        #Standard practice to respond to POST requests with redirect
        #as web browsers refresh by re-issuing the last request.
        #Without redirecting, refresh will resubmit the form.

        return redirect(request.referrer)
    return redirect(request.referrer)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index', username = current_user.username))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index', username = current_user.username))
    user = User.verify_reset_password_token(token)
    if not user: #If token is invalid
        return redirect(url_for('index', username = current_user.username))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)



@app.route('/search', methods = ['POST'])
@login_required
def search():
    form0 = SearchProfileForm()
    if form0.validate_on_submit():
        user = User.query.filter_by(username = form0.username.data).first()
        if user is not None:
            return redirect(url_for('user', username = user.username))
    flash('Invalid Username')
    return redirect(request.referrer)


@app.route('/edit_profile/<username>', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    user = User.query.filter_by(username = username).first_or_404()
    if current_user == user or current_user.id == 1:
        form = EditProfileForm(current_user.username)
        if form.validate_on_submit(): #When submit button is clicked
            user.username = form.username.data
            user.about_me = form.about_me.data
            db.session.commit()
            flash('Your changes have been saved.')
            return redirect(url_for('user', username = user.username))
        elif request.method == 'GET': #Before submit button is clicked
            form.username.data = user.username
            form.about_me.data = user.about_me
        return render_template('edit_profile.html', title='Edit Profile',
                               form=form, user = user)
    else:
        return redirect(url_for('index', username = current_user.username))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password invalid')
            return redirect(url_for('change_password'))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '': #Security reasons
            next_page = url_for('user', username=current_user.username)
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password changed successfully')
        return redirect(next_page)
    return render_template('change_password.html', title='Change password', form=form)
            

@app.route('/handle_follow/<string:username>', methods = ['POST'])
def handle_follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = username).first()
        if user is None:
            flash('User ' + username + ' not found')
            return redirect(request.referrer)
        if current_user == user:
            flash('You cannot follow or unfollow yourself')
            return redirect(request.referrer)
        if current_user.is_following(user):
            current_user.unfollow(user)
            flash('You have unfollowed ' + username)
        else:
            current_user.follow(user)
            flash('You are now following ' + username)
        db.session.commit()
        return redirect(request.referrer)
    return redirect(request.referrer)


def assign_badge(author):
    if author.upvotes > 4:
        author.badge = 'Viking'
    elif author.upvotes > 3:
        author.badge = 'Hero'
    elif author.upvotes > 2:
        author.badge = 'Daredevil'
    elif author.upvotes > 1:
        author.badge = 'Fearless'
    elif author.upvotes > 0:
        author.badge = 'Brave'
    else:
        author.badge = 'Rookie'

@app.route('/vote/<int:post_id>', methods = ['POST'])
@login_required
def vote(post_id):
    form = EmptyForm() 
    if form.validate_on_submit():
        post = Post.query.get_or_404(post_id)
        check_voted = Upvote.query.filter_by(post = post, user = current_user).first()
        if check_voted:
            post.votes = post.votes - 1
            post.author.upvotes -= 1
            db.session.delete(check_voted)
            db.session.commit()
            flash('Downvoted! :(')
        else:
            post.votes = post.votes + 1
            post.author.upvotes += 1
            new_vote = Upvote(post = post, user = current_user)
            db.session.add(new_vote)
            db.session.commit()
            flash('Upvoted! :)')
        assign_badge(post.author)
        db.session.commit()
        return redirect(request.referrer) #goes to the url the referred u here, have redirect after every successful post good habit, as may cause issues in refresh
    return redirect(request.referrer) #csrf token expired or invalid


@app.route('/open_video/<int:post_id>')#from post_dare as url var change in opendare
@login_required
def open_video(post_id):
    try: 
        post = Post.query.get_or_404(post_id)
        user = post.author
        '''
        directory = app.config['UPLOAD_FOLDER'] + '/' + str(user.id) + '_' + user.username
        return send_from_directory(directory, filename = post.dare, as_attachment = False)
        '''
        print('open filename: ' + post.dare)
        return fbStorage.child(post.dare).get_url(None)
    except FileNotFoundError:
        abort(404)


@app.route('/comments/<post_id>', methods=['GET', 'POST'])#put the prev page so that can delete dare
@login_required
def comments(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form0 = SearchProfileForm()
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.comment.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('comments', post_id=post.id))
    
    page = request.args.get('page', 1, type=int)    
    comments = Comment.query.order_by(Comment.timestamp.desc()).filter_by(post=post).paginate(
        page, app.config['COMMENTS_PER_PAGE'], False)
        
    next_url = url_for('comments', post_id=post.id, page=comments.next_num) \
        if comments.has_next else None
    prev_url = url_for('comments', post_id=post.id, page=comments.prev_num) \
        if comments.has_prev else None
    
    return render_template('comments_section.html', title='Comments', upvote=Upvote,
                            form0=form0, form=form, post=post, comments=comments.items, fbStorage = fbStorage, prev_url = prev_url, next_url = next_url)


@app.route('/delete_comment/<comment_id>', methods=['POST'])
@login_required                            
def delete_comment(comment_id):
    form = EmptyForm()
    if form.validate_on_submit():
        comment = Comment.query.filter_by(id=comment_id).first_or_404()
        reports = Report.query.filter_by(comment=comment).all()
        post = comment.post
        for report in reports:
            db.session.delete(report)
        db.session.delete(comment)
        db.session.commit()
        flash('Your comment has been deleted!')
        return redirect(url_for('comments', post_id=post.id))
    else: #CSRF token missing or invalid
        return redirect(request.referrer)


@app.route('/delete_post/<post_id>', methods=['POST'])
@login_required                            
def delete_post(post_id):
    form = EmptyForm()
    if form.validate_on_submit():
        post = Post.query.filter_by(id=post_id).first_or_404()
        original_poster = post.author
        comments = Comment.query.filter_by(post=post).all()
        upvotes = Upvote.query.filter_by(post=post).all()
        reports = Report.query.filter_by(post=post).all()
        post.author.upvotes -= len(upvotes)#minus off number of upvotes
        for comment in comments:
            db.session.delete(comment)
        for upvote in upvotes:
            db.session.delete(upvote)
        for report in reports:
            db.session.delete(report)
 #so tht go prev page           
        prev_url = ''
        try:
            prev_url = request.args.get('prev') #only if come from comments
            if url_parse(prev_url).netloc != '':
                prev_url = url_for('index', username = current_user.username)
        except:
            prev_url = request.referrer


        assign_badge(post.author)
        db.session.delete(post)
        db.session.commit()
        
        '''
        user = post.author
        local_path = app.config['UPLOAD_FOLDER']
        delete_file_path = local_path + '/' + str(user.id) + '_' + user.username
        os.chdir(delete_file_path)
        os.remove(post.dare)
        os.chdir(app.config['TOP_LEVEL'])
        '''
        
        flash('Your post has been deleted!')
        return redirect(prev_url)
    else: #CSRF token missing or invalid
        return redirect(request.referrer)      


@app.route('/explore')
@login_required
def explore():
    form0 = SearchProfileForm()
    form = EmptyForm()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).filter_by(banned=0).paginate(
        page, app.config['POSTS_PER_PAGE'], False) #Getting all posts
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('explore.html', title='Explore', form=form, posts=posts.items, upvote=Upvote, next_url=next_url, prev_url=prev_url, form0 = form0, fbStorage = fbStorage)
                    

@app.route('/leaderboard')
@login_required
def leaderboard():
    form0 = SearchProfileForm()
    form = EmptyForm()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.votes.desc()).filter_by(banned=0).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('leaderboard', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('leaderboard', page=posts.prev_num) \
        if posts.has_prev else None
    page_num = request.args.get('page', '1')
    start_num = int(page_num) * app.config['POSTS_PER_PAGE'] - app.config['POSTS_PER_PAGE'] + 1
    return render_template('leaderboard.html', title='Leaderboard', form=form, posts=posts.items, upvote=Upvote, next_url=next_url, prev_url=prev_url, start_num=start_num, form0 = form0, fbStorage = fbStorage)


@app.route('/specific_report/<int:id>', methods = ['GET', 'POST'])##change all post/comment/profile to specific report and to have prev that contain post/comment/profile
@login_required                            
def specific_report(id):##all specific reports come here
    form = ReportForm()
    if form.validate_on_submit():
        prev_url = request.args.get('prev')
        report_type = request.args.get('type')
        if url_parse(prev_url).netloc != '':
            return redirect('index', username = current_user.username)
        report = ''
        if report_type.find('profile') != -1:
            report = Report(reason=form.reason.data, author=current_user, user=User.query.filter_by(id = id).first())
        elif report_type.find('comment') != -1:
            report = Report(reason=form.reason.data, author=current_user, comment=Comment.query.filter_by(id = id).first())
        else:
            report = Report(reason=form.reason.data, author=current_user, post=Post.query.filter_by(id = id).first())
        db.session.add(report)
        db.session.commit()
        flash('Thanks for your feedback!')
        return redirect(prev_url)
    return render_template('report.html', title='Report',
                           form=form)
       

@app.route('/general_report', methods = ['GET', 'POST'])
@login_required
def general_report():
    form = ReportForm()
    if form.validate_on_submit():
        prev_url = request.args.get('prev')
        if url_parse(prev_url).netloc != '':
            return redirect(url_for('index', username = current_user.username))
        report = Report(reason = form.reason.data, page_of_report = prev_url, author = current_user)
        db.session.add(report)
        db.session.commit()
        flash('Your report has been submitted. Thank you for your feedback')
        return redirect(prev_url)
    return render_template('gen_report.html', form = form, title = 'Report')


@app.route('/dismiss_case/<id>', methods=['POST'])#also add prev
@login_required
def dismiss_case(id):
    form = EmptyForm()
    if form.validate_on_submit():
        report_type = request.args.get('prev')
        reports = ''
        if report_type == 'post':
            reports = Report.query.filter_by(post_id=id).all()
        elif report_type == 'comment':
            reports = Report.query.filter_by(comment_id=id).all()
        elif report_type == 'user':
            reports = Report.query.filter_by(profile_id = id).all()
        else:
            reports = Report.query.filter_by(id=id).all()
        for report in reports:
            db.session.delete(report)
        db.session.commit()
        flash("Case dismissed")
        return redirect(request.referrer)


@app.route('/ban_comment/<comment_id>', methods=['POST'])#try with comments 1st
@login_required
def ban_comment(comment_id):
    form = BanForm()
    if form.validate_on_submit():
        reports = Report.query.filter_by(comment_id=comment_id).all()
        comment = Comment.query.filter_by(id=comment_id).first_or_404()
        comment.banned = 1
        comment.ban_reason = form.reason.data
        comment.author.demerits += 1
        for report in reports:
            db.session.delete(report)
            #report.seen = 1
            #report.action_taken = form.reason.data
        db.session.commit()
        flash("Case resolved")
        return redirect(request.referrer)
    return redirect(url_for('index', username = current_user.username))


@app.route('/ban_post/<post_id>', methods=['POST'])
@login_required
def ban_post(post_id):
    form = BanForm()
    if form.validate_on_submit():
        reports = Report.query.filter_by(post_id=post_id).all()
        post = Post.query.filter_by(id=post_id).first_or_404()
        post.banned = 1
        post.ban_reason = form.reason.data
        post.author.upvotes -= post.votes
        post.author.demerits += 1
        assign_badge(post.author)
        for report in reports:
            db.session.delete(report)
        db.session.commit()
        flash("Case resolved")
        return redirect(request.referrer)
    return redirect(url_for('index', username = current_user.username))


@app.route('/ban_profile/<profile_id>', methods = ['POST'])
@login_required
def ban_profile(profile_id):
    form = BanForm()
    if form.validate_on_submit():
        reports = Report.query.filter_by(profile_id=profile_id).all()
        profile = User.query.filter_by(id=profile_id).first_or_404()
        profile.banned = 1
        profile.ban_reason = form.reason.data
        profile.demerits += 1
        for report in reports:
            db.session.delete(report)
        db.session.commit()
        flash("Case resolved")
        return redirect(request.referrer)
    return redirect(url_for('index', username = current_user.username))

@app.route('/action/<id>', methods=['POST'])
@login_required
def action(id):
    form = ReportForm()
    if form.validate_on_submit():
        report = Report.query.get_or_404(id)
        report.action_taken = form.reason.data
        report.seen = 1
        db.session.commit()
        return redirect(request.referrer)
    return redirect(url_for('index', username = current_user.username))


@app.route('/reported_posts', methods=['GET', 'POST'])
@login_required
def reported_posts():
    form0 = SearchProfileForm()
    form = EmptyForm()
    form2 = BanForm()
    if current_user.id == 1:
        page = request.args.get('page', 1, type=int)
     #not displaying by report, but by post#################check how
        posts = Post.query.filter(Post.reports != None).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('reported_cases', page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('reported_cases', page=posts.prev_num) \
            if posts.has_prev else None
        return render_template('reported_posts.html', title='Reported Posts', posts=posts.items,
                                form=form, form2=form2, next_url=next_url, prev_url=prev_url, form0 = form0, fbStorage = fbStorage)
    return render_template('admin_restricted.html')


@app.route('/reported_comments', methods=['GET', 'POST'])
@login_required
def reported_comments():
    form0 = SearchProfileForm()
    form = EmptyForm()
    form2 = BanForm()
    if current_user.id == 1:
        page = request.args.get('page', 1, type=int)
        comments = Comment.query.filter(Comment.reports != None).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('reported_cases', page=comments.next_num) \
            if comments.has_next else None
        prev_url = url_for('reported_cases', page=comments.prev_num) \
            if comments.has_prev else None
        return render_template('reported_comments.html', title='Reported Comments', 
                                comments=comments.items, form=form, form2=form2, 
                                next_url=next_url, prev_url=prev_url, form0 = form0)
    return render_template('admin_restricted.html')
        

@app.route('/reported_users', methods=['GET', 'POST'])
@login_required
def reported_users():
    form0 = SearchProfileForm()
    form = EmptyForm()
    form2 = BanForm()
    if current_user.id == 1:
        page = request.args.get('page', 1, type=int)
        users = User.query.filter(User.reports_on_me != None).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('reported_cases', page=users.next_num) \
            if users.has_next else None
        prev_url = url_for('reported_cases', page=users.prev_num) \
            if users.has_prev else None
        return render_template('reported_users.html', title='Reported Users', 
                                users=users.items, form=form, form2=form2, 
                                next_url=next_url, prev_url=prev_url, form0 = form0)
    return render_template('admin_restricted.html')
 

@app.route('/reported_general', methods = ['GET']) #2 issues, if person clicks report after clicking report, then the prev page is now report and the home page goes to admin hime and not the person home
def reported_general():
    form0 = SearchProfileForm()
    form = EmptyForm()
    #form2 = ReportForm()
    page = request.args.get('page', 1, type = int)
    reports = Report.query.filter(Report.page_of_report != None).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('reported_general', page = reports.next_num)\
    if reports.has_next else None
    prev_url = url_for('reported_general', page = reports.prev_num)\
    if reports.has_prev else None
    return render_template('reported_gen.html', reports = reports.items, form = form, prev_url = prev_url, next_url = next_url, title = 'Reported General', form0 = form0)


@app.route('/post_report_reasons/<post_id>', methods=['GET'])
@login_required
def post_report_reasons(post_id):
    if current_user.id == 1:
        post = Post.query.filter_by(id=post_id).first_or_404() 
        page = request.args.get('page', 1, type=int)    
        reports = Report.query.order_by(Report.timestamp.desc()).filter_by(post=post).paginate(
            page, app.config['COMMENTS_PER_PAGE'], False)
            
        next_url = url_for('post_report_reasons', post_id=post.id, page=reports.next_num) \
            if reports.has_next else None
        ###change post
        prev_url = url_for('post_report_reasons', post_id=post.id, page=reports.prev_num) \
            if reports.has_prev else None

        return render_template('report_reasons.html', title='Reasons for report', reports=reports.items)
    return render_template('admin_restricted.html')


@app.route('/comment_report_reasons/<comment_id>', methods=['GET'])
@login_required
def comment_report_reasons(comment_id):
    if current_user.id == 1:
        comment = Comment.query.filter_by(id=comment_id).first_or_404() 
        page = request.args.get('page', 1, type=int)    
        reports = Report.query.order_by(Report.timestamp.desc()).filter_by(comment=comment).paginate(
            page, app.config['COMMENTS_PER_PAGE'], False)
             
        next_url = url_for('report_reasons', post_id=post.id, page=reports.next_num) \
            if reports.has_next else None
        prev_url = url_for('report_reasons', post_id=post.id, page=reports.prev_num) \
            if reports.has_prev else None

        return render_template('report_reasons.html', title='Reasons for report', reports=reports.items)
    return render_template('admin_restricted.html')


@app.route('/user_report_reasons/<user_id>', methods=['GET'])
@login_required
def user_report_reasons(user_id):
    if current_user.id == 1:
        user = User.query.filter_by(id=user_id).first_or_404() 
        page = request.args.get('page', 1, type=int)    
        reports = Report.query.order_by(Report.timestamp.desc()).filter_by(user=user).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
             
        next_url = url_for('report_reasons', post_id=post.id, page=reports.next_num) \
            if reports.has_next else None
        prev_url = url_for('report_reasons', post_id=post.id, page=reports.prev_num) \
            if reports.has_prev else None

        return render_template('report_reasons.html', title='Reasons for report', reports=reports.items)
    return render_template('admin_restricted.html')


@app.route('/messages/<username>', methods = ['GET', 'POST'])
@login_required
def messages(username):
    msg_to = User.query.filter_by(username = username).first_or_404()
    form0 = SearchProfileForm()
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(body = form.message.data, author = current_user, profile = msg_to)
        db.session.add(message)
        flash('Message sent!')

    ##add change to table
        prev_convo = None
        new_convo = None
        try:
            print('curstart')
            current_start = Conversation.query.filter_by(author = current_user, profile = msg_to)
            print('msgstart')
            msg_to_start = Conversation.query.filter_by(author = msg_to, profile = current_user)
            print('union')
            prev_convo = current_start.union(msg_to_start).first()
            print('set_tm')
            prev_convo.timestamp = message.timestamp
            print('finish try')
        except:
            print('new convo')
            new_convo = Conversation(author = current_user, profile = msg_to)
            db.session.add(new_convo)


        db.session.commit()
        return redirect(url_for('messages', username = username))
    page = request.args.get('page', 1, type=int)
   # namelist = [ current_user.username, msg_to.username ]
   # messages = Message.query.filter(Message.author = current_user, profile = msg_to).order_by(Message.timestamp.desc()).paginate(page, app.config['MESSAGES_PER_PAGE'], False)
    messages = current_user.msgs_btw(username).paginate(page, app.config['MESSAGES_PER_PAGE'], False)
    
    for message in messages.items:
        if message.author != current_user:
            message.seen = 1    
    db.session.commit()
    
    next_url = url_for('messages', username = username, page = messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages', username = username, page = messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', title = 'Messages', messages = messages.items, form0 = form0, form = form, user = msg_to, prev_url = prev_url, next_url = next_url)


@app.route('/messages_section/<username>')
@login_required
def messages_section(username):
    form0 = SearchProfileForm()
    page = request.args.get('page', 1, type = int)
    convos = Conversation.query.filter_by(author = current_user).union(Conversation.query.filter_by(profile = current_user)).order_by(Conversation.timestamp.desc()).paginate(page, app.config['CONVERSATIONS_PER_PAGE'], False)

    next_url = url_for('messages_section', username = username, page = convos.next_num) \
        if convos.has_next else None
    prev_url = url_for('messages_section', username = username, page = convos.prev_num) \
        if convos.has_prev else None

    convos_with = []
    for convo in convos.items:
        if convo.author == current_user:
            convos_with.append(convo.profile)
        else:
            convos_with.append(convo.author)

    return render_template('messages_section.html', convos_with = convos_with, next_url = next_url, prev_url = prev_url, form0 = form0, Message = Message)

    '''
    messages_with = []
    all_messaged = current_user.messaged.union(current_user.messengers).paginate(page, app.config['MESSAGES_PER_PAGE'], False)
    
    next_url = url_for('messages_section', username = username, page = all_messaged.next_num) \
        if all_messaged.has_next else None
    prev_url = url_for('messages_section', username = username, page = all_messaged.prev_num) \
        if all_messaged.has_prev else None

    return render_template('messages_section.html', all_messaged = all_messaged.items, next_url = next_url, prev_url = prev_url, form0 = form0)
    '''    
    '''
    messages = current_user.messages_from.union(current_user.messages_to).order_by(Message.timestamp.desc()).paginate(page, app.config['MESSAGES_PER_PAGE'], False)
    next_url = url_for('messages_section', username = username, page = messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages_section', username = username, page = messages.prev_num) \
        if messages.has_prev else None
    '''

    #return render_template('messages_section.html', messages = messages.items, next_url = next_url, prev_url = prev_url)


