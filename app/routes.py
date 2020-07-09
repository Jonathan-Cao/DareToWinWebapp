from flask import render_template, flash, redirect, request, url_for, send_from_directory, abort
import os
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, EditProfileForm, ChangePasswordForm, EmptyForm, PostForm, CommentForm, ReportForm, BanForm, SearchProfileForm
from app.email import send_password_reset_email
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post, Comment, Upvote, Report
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse 
from datetime import datetime

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
    if current_user.banned:
        return render_template('banned.html')
    return render_template('explore.html', title='Explore', form=form, form0=form0, posts=posts.items,
                            upvote=Upvote, next_url=next_url, prev_url=prev_url)
                            
@app.route('/leaderboard')
@login_required
def leaderboard():
    form0 = SearchProfileForm()
    form = EmptyForm()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.votes.desc()).filter_by(banned=0).paginate(
        page, app.config['POSTS_PER_PAGE'], False) #Getting all posts
    next_url = url_for('leaderboard', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('leaderboard', page=posts.prev_num) \
        if posts.has_prev else None
    page_num = request.args.get('page', '1')
    start_num = int(page_num) * app.config['POSTS_PER_PAGE'] - app.config['POSTS_PER_PAGE'] + 1
    if current_user.banned:
        return render_template('banned.html')
    return render_template('leaderboard.html', title='Leaderboard', form=form, form0=form0,
                            posts=posts.items, upvote=Upvote, next_url=next_url, 
                            prev_url=prev_url, start_num=start_num)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    #Submit post
    form0 = SearchProfileForm()
    form = EmptyForm()
    form2 = PostForm()
    if form.validate_on_submit():
        file = form2.dare.data
        post = Post(body=form2.post.data, author=current_user)     
        db.session.add(post)
        post = Post.query.order_by(Post.timestamp.desc()).first()
        filename = secure_filename("{}_{}_{}".format(
                    str(post.author.id), str(post.author), str(post.id)))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #path = str(app.config['UPLOAD_FOLDER'] + "/" + filename)
        post.dare = filename
        db.session.commit()
        flash('Your post is now live!')
        #Standard practice to respond to POST requests with redirect
        #as web browsers refresh by re-issuing the last request.
        #Without redirecting, refresh will resubmit the form.
        return redirect(url_for('index'))        
    #Page navigation
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().filter_by(banned=0).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    if current_user.banned:
        return render_template('banned.html')
    return render_template('index.html', title='Home', form=form, form2=form2, form0=form0,
                            posts=posts.items, upvote=Upvote,
                            next_url=next_url, prev_url=prev_url)
                            
@app.route('/reported_posts', methods=['GET', 'POST'])
@login_required
def reported_posts():
    form0 = SearchProfileForm()
    form = EmptyForm()
    form2 = BanForm()
    if current_user.id == 1:
        page = request.args.get('page', 1, type=int)
        posts = Post.query.filter(Post.reports != None).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('reported_posts', page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('reported_posts', page=posts.prev_num) \
            if posts.has_prev else None
        return render_template('reported_posts.html', title='Reported Posts', posts=posts.items,
                                form=form, form2=form2, form0=form0,
                                next_url=next_url, prev_url=prev_url)
    return render_template('admin_restricted.html')
                            
@app.route('/post_report_reasons/<post_id>', methods=['GET'])
@login_required
def post_report_reasons(post_id):
    if current_user.id == 1:
        post = Post.query.filter_by(id=post_id).first_or_404() 
        page = request.args.get('page', 1, type=int)    
        reports = Report.query.order_by(Report.timestamp.desc()).filter_by(post=post).paginate(
            page, app.config['COMMENTS_PER_PAGE'], False)
            
        next_url = url_for('report_reasons', post_id=post.id, page=reports.next_num) \
            if reports.has_next else None
        prev_url = url_for('report_reasons', post_id=post.id, page=reports.prev_num) \
            if reports.has_prev else None

        return render_template('report_reasons.html', title='Reasons for report',
                                reports=reports.items)
    return render_template('admin_restricted.html')
        
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
        return render_template('reported_comments.html', title='Reported Posts', 
                                comments=comments.items, form=form, form2=form2, form0=form0,
                                next_url=next_url, prev_url=prev_url)
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

        return render_template('report_reasons.html', title='Reasons for report',
                                reports=reports.items)
    return render_template('admin_restricted.html')

@app.route('/ban_comment/<comment_id>', methods=['POST'])
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
        db.session.commit()
        flash("Case resolved")
        return redirect(request.referrer)
        
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
        next_url = url_for('reported_users', page=users.next_num) \
            if users.has_next else None
        prev_url = url_for('reported_users', page=users.prev_num) \
            if users.has_prev else None
        return render_template('reported_users.html', title='Reported Users', 
                                users=users.items, form=form, form2=form2, 
                                next_url=next_url, prev_url=prev_url, form0 = form0)
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
    
@app.route('/ban_profile/<profile_id>', methods = ['POST'])
@login_required
def ban_profile(profile_id):
    form = BanForm()
    if form.validate_on_submit():
        reports = Report.query.filter_by(profile_id=profile_id).all()
        profile = User.query.filter_by(id=profile_id).first_or_404()
        profile.about_me = "About me removed due to: {}".format(form.reason.data)
        profile.ban_reason = form.reason.data
        profile.demerits += 1
        for report in reports:
            db.session.delete(report)
        db.session.commit()
        flash("Case resolved")
        return redirect(request.referrer)
    return redirect(url_for('index'))
    
@app.route('/dismiss_case/<id>', methods=['POST'])
@login_required
def dismiss_case(id):
    form = EmptyForm()
    if form.validate_on_submit():
        report_type = request.args.get('type')
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

@app.route('/open_video/<post_dare>')
@login_required
def open_video(post_dare):
    try:
        directory = app.config['UPLOAD_FOLDER']
        filename = post_dare
        return send_from_directory(directory, filename=filename)
    except FileNotFoundError:
        abort(404)
        
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
        post.author.upvotes -= len(upvotes)
        os.remove(app.config['UPLOAD_FOLDER'] +  '/' + post.dare)
        for comment in comments:
            db.session.delete(comment)
        for upvote in upvotes:
            db.session.delete(upvote)
        for report in reports:
            db.session.delete(report) 
        assign_badge(post.author)
        db.session.delete(post)
        db.session.commit()
        flash('Your post has been deleted!')
        return redirect(request.referrer)
    else: #CSRF token missing or invalid
        return redirect(request.referrer)
        
@app.route('/specific_report/<id>', methods=['GET', 'POST'])
@login_required                            
def specific_report(id):
    form = ReportForm()
    if form.validate_on_submit():
        prev_url = request.args.get('prev')
        report_type = request.args.get('type')
        if url_parse(prev_url).netloc != '':
            return redirect('index')
        if report_type.find('post') != -1:
            report = Report(reason=form.reason.data, author=current_user, post_id=id)
        elif report_type.find('comment') != -1:
            report = Report(reason=form.reason.data, author=current_user, comment_id=id)
        else:
            report = Report(reason=form.reason.data, author=current_user, profile_id=id)
        db.session.add(report)
        db.session.commit()
        flash('Thanks for your feedback!')
        return redirect(prev_url)
    return render_template('report.html', title='Report',
                           form=form)

@app.route('/upvote/<post_id>', methods=['POST'])
@login_required
def upvote(post_id):
    form = EmptyForm()
    if form.validate_on_submit():
        post = Post.query.filter_by(id=post_id).first_or_404()
        upvote = Upvote(upvoter_id=current_user.id, post=post)
        db.session.add(upvote)
        #Assigning badge
        post.author.upvotes += 1
        post.votes += 1
        assign_badge(post.author)
        db.session.commit()
        flash('Upvoted! :)')
        return redirect(request.referrer)
        
@app.route('/downvote/<post_id>', methods=['POST'])
@login_required
def downvote(post_id):
    form = EmptyForm()
    if form.validate_on_submit():
        post = Post.query.filter_by(id=post_id).first_or_404()
        upvote = Upvote.query.filter_by(upvoter_id=current_user.id, post=post).first_or_404()
        db.session.delete(upvote)
        #Assigning badge
        post.author.upvotes -= 1
        post.votes -= 1
        assign_badge(post.author)
        db.session.commit()
        flash('Downvoted! :(')
        return redirect(request.referrer)

@app.route('/comments/<post_id>', methods=['GET', 'POST'])
@login_required
def comments(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.comment.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        #Standard practice to respond to POST requests with redirect
        #as web browsers refresh by re-issuing the last request.
        #Without redirecting, refresh will resubmit the form.
        return redirect(url_for('comments', post_id=post.id))
    
    page = request.args.get('page', 1, type=int)    
    comments = Comment.query.order_by(Comment.timestamp.desc()).filter_by(post=post).paginate(
        page, app.config['COMMENTS_PER_PAGE'], False)
        
    next_url = url_for('comments', post_id=post.id, page=posts.next_num) \
        if comments.has_next else None
    prev_url = url_for('comments', post_id=post.id, page=posts.prev_num) \
        if comments.has_prev else None
    
    return render_template('comments_section.html', title='Comments', upvote=Upvote,
                            form=form, post=post, comments=comments.items)

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
        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: 
		#Already logged in
	    return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '': #Security reasons
            next_page = url_for('index')
        return redirect(next_page)
        """
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
        """
    return render_template('login.html', title='Sign In', form=form)
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
    
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
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
    
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

@app.route('/user/<username>') #Profile
@login_required
def user(username):
    form0 = SearchProfileForm()
    form = EmptyForm() #Follow/Unfollow button
    form2 = BanForm()
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.own_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    if user.banned and current_user.id != 1:
        return render_template('banned.html')
    return render_template('user.html', user=user, form=form, form2=form2, form0=form0,
                            posts=posts.items, upvote=Upvote, next_url=next_url, prev_url=prev_url)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user: #If token is invalid
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.before_request 
#Set last seen by overwriting with current time whenever that user sends a request to the server
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        #No need for db.session.add() as load_user function in models.py already puts
        #target user in database session.
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit(): #When submit button is clicked
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET': #Before submit button is clicked
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
                           
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
    
@app.route('/following/<username>', methods=['GET', 'POST'])
@login_required
def following(username):
    form = EmptyForm()
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    following = user.followed.paginate(
        page, app.config['COMMENTS_PER_PAGE'], False)
    next_url = url_for('following', username=user.username, page=following.next_num) \
        if following.has_next else None
    prev_url = url_for('following', username=user.username, page=following.prev_num) \
        if following.has_prev else None
    return render_template('following.html', form=form, user=user, following=following.items,
                            next_url=next_url, prev_url=prev_url)
    
@app.route('/followers/<username>', methods=['GET', 'POST'])
@login_required
def followers(username):
    form = EmptyForm()
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    followers = user.followers.paginate(
        page, app.config['COMMENTS_PER_PAGE'], False)
    next_url = url_for('followers', username=user.username, page=followers.next_num) \
        if followers.has_next else None
    prev_url = url_for('followers', username=user.username, page=followers.prev_num) \
        if followers.has_prev else None
    return render_template('followers.html', form=form, user=user, followers=followers.items,
                            next_url=next_url, prev_url=prev_url)
                           
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are now following {}!'.format(username))
        return redirect(request.referrer)
    else: #CSRF token missing or invalid
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are no longer following {}.'.format(username))
        return redirect(request.referrer)
    else: #CSRF token missing or invalid
        return redirect(url_for('index'))
