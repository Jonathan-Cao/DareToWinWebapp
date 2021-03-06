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

#colour of the badge assigned based on total number of upvotes the user has
badge_colour = {'Rookie': "label label-default",
                'Brave': "label label-warning",
                'Fearless': "label label-info",
                'Daredevil': "label label-danger",
                'Hero': "label label-success",
                'Viking': "label label-primary"}

#allows users to see the latest videos uploaded by all users
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
                            upvote=Upvote, badge_colour=badge_colour, next_url=next_url, prev_url=prev_url)

#allows users to see the dares with the highest votes in descending order
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
                            posts=posts.items, upvote=Upvote, badge_colour=badge_colour,
                            next_url=next_url, prev_url=prev_url, start_num=start_num)

#homepage of the webapp, which allows users to upload and view their feed
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
                            posts=posts.items, upvote=Upvote, badge_colour=badge_colour,
                            next_url=next_url, prev_url=prev_url)

#allows admistrators to view general bugs/issues that users face and solve them if need be
@app.route('/reported_general', methods = ['GET', 'POST'])
@login_required
def reported_general():
    form0 = SearchProfileForm()
    form = EmptyForm()
    if current_user.id == 1:
        page = request.args.get('page', 1, type = int)
        reports = Report.query.filter(Report.page_of_report != None).paginate(page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('reported_general', page = reports.next_num) \
            if reports.has_next else None
        prev_url = url_for('reported_general', page = reports.prev_num)\
            if reports.has_prev else None
        return render_template('reported_general.html', reports = reports.items, form = form, 
                                prev_url = prev_url, next_url = next_url, 
                                badge_colour=badge_colour, title = 'Reported General', form0 = form0)
    return render_template('admin_restricted.html')

#allows admistrators to view posts that have been reported and ban them if need be
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
                                form=form, form2=form2, form0=form0, badge_colour=badge_colour,
                                next_url=next_url, prev_url=prev_url)
    return render_template('admin_restricted.html')

#allows admistrators to view the reasons as to why this post was reported
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
                                badge_colour=badge_colour, reports=reports.items)
    return render_template('admin_restricted.html')

#allows admistrators to ban posts that are deemed inappropriate
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

#allows admistrators to view comments that have been reported and ban them if need be
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
                                badge_colour=badge_colour, next_url=next_url, prev_url=prev_url)
    return render_template('admin_restricted.html')

#allows admistrators to view the reasons as to why this comment was reported
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
                                badge_colour=badge_colour, reports=reports.items)
    return render_template('admin_restricted.html')

#allows admistrators to ban comments that are deemed inappropriate
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

#allows admistrators to view users that have been reported and ban them if need be
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
        return render_template('reported_users.html', title='Reported Users', badge_colour=badge_colour,
                                users=users.items, form=form, form2=form2, 
                                next_url=next_url, prev_url=prev_url, form0 = form0)
    return render_template('admin_restricted.html')

#allows admistrators to view the reasons as to why this user was reported
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

        return render_template('report_reasons.html', title='Reasons for report', 
                                badge_colour=badge_colour, reports=reports.items)
    return render_template('admin_restricted.html')

#allows admistrators to ban userss that are deemed inappropriate
@app.route('/ban_profile/<profile_id>', methods = ['POST'])
@login_required
def ban_profile(profile_id):
    form = BanForm()
    if form.validate_on_submit():
        reports = Report.query.filter_by(profile_id=profile_id).all()
        profile = User.query.filter_by(id=profile_id).first_or_404()
        profile.banned = 1
        profile.ban_reason = form.reason.data
        for report in reports:
            db.session.delete(report)
        db.session.commit()
        flash("Case resolved")
        return redirect(request.referrer)
    return redirect(url_for('index'))

#allows admistrators to dismiss any report where the content reported is deemed appropriate
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

#allows users to watch the dare video uploaded
@app.route('/open_video/<post_dare>')
@login_required
def open_video(post_dare):
    try:
        directory = app.config['UPLOAD_FOLDER']
        filename = post_dare
        return send_from_directory(directory, filename=filename)
    except FileNotFoundError:
        abort(404)

#assigns badge to the user based on the total number of upvotes for that user
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

#allows users to delete their post
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

#allows users to report other users' dare/comment/profile to admistrators
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
        flash('Your report has been submitted. Thank you for your feedback!')
        return redirect(prev_url)
    return render_template('specific_report.html', title='Report',
                           form=form)

#allows users to report general bugs/issues in the webapp to admistrators
@app.route('/general_report', methods = ['GET', 'POST'])
@login_required
def general_report():
    form0 = SearchProfileForm()
    form = ReportForm()
    if form.validate_on_submit():
        prev_url = request.args.get('prev')
        if url_parse(prev_url).netloc != '':
            return redirect(url_for('index'))
        report = Report(reason = form.reason.data, page_of_report = prev_url, author = current_user)
        db.session.add(report)
        db.session.commit()
        flash('Your report has been submitted. Thank you for your feedback!')
        return redirect(prev_url)
    return render_template('general_report.html', form = form, form0=form0, title='Report')

#allows users to upvote other users' dare videos
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

#allows users to downvote other users' dare videos
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

#allows users to comment on posts and also view the comment section of the posts
@app.route('/comments/<post_id>', methods=['GET', 'POST'])
@login_required
def comments(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form = CommentForm()
    form0 = SearchProfileForm()
    if form.validate_on_submit():
        comment = Comment(body=form.comment.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('comments', post_id=post.id))
    
    page = request.args.get('page', 1, type=int)    
    comments = Comment.query.order_by(Comment.timestamp.desc()).filter_by(post=post).paginate(
        page, app.config['COMMENTS_PER_PAGE'], False)
        
    next_url = url_for('comments', post_id=post.id, page=posts.next_num) \
        if comments.has_next else None
    prev_url = url_for('comments', post_id=post.id, page=posts.prev_num) \
        if comments.has_prev else None
    
    return render_template('comments_section.html', title='Comments', upvote=Upvote,
                            badge_colour=badge_colour, form=form, form0=form0, 
                            post=post, comments=comments.items)

#allows users to delete their comment
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

#allows users to login to their account
@app.route('/', methods=['GET', 'POST'])
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

#allows users to logout of their account
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

#allows users to register their account
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

#allows users to search users' profiles
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

#allows users to view users' profiles
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
                            posts=posts.items, upvote=Upvote, badge_colour=badge_colour,
                            next_url=next_url, prev_url=prev_url)

#allows users to reset their password
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

#checks if the reset password token provided by the user is valid, and if so, allows them to reset password
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

#Set last seen by overwriting with current time whenever that user sends a request to the server,
#and alerts user if he has any messages
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        #No need for db.session.add() as load_user function in models.py already puts
        #target user in database session.
        messages = current_user.messages_to.union(current_user.messages_from)
        total_flashes = 0
        for message in messages:
            if message.flashed == 0 and message.author != current_user:
                total_flashes += 1
                message.flashed = 1
        if total_flashes > 0:
            flash('You have ' + str(total_flashes) + ' new messages!')
        db.session.commit()

#allows users to edit their username and 'About me'
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
                           
#allows users to change their passwords
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

#allows users to view all the users the specified user is following
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
                            badge_colour=badge_colour, next_url=next_url, prev_url=prev_url)

#allows users to view the specified user's followers
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
                            badge_colour=badge_colour, next_url=next_url, prev_url=prev_url)

#allows users to follow the specified user
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

#allows users to unfollow the specified user
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

#allows the user to view all the private conversations they are involved in
@app.route('/messages_section/<username>')
@login_required
def messages_section(username):
    form0 = SearchProfileForm()
    page = request.args.get('page', 1, type = int)
    convos = Conversation.query.filter_by(
        author = current_user).union(
        Conversation.query.filter_by(
        profile = current_user)).order_by(
        Conversation.timestamp.desc()).paginate(page, app.config['CONVERSATIONS_PER_PAGE'], False)

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

    return render_template('messages_section.html', convos_with = convos_with, 
                            next_url = next_url, prev_url = prev_url, 
                            badge_colour=badge_colour, form0 = form0, Message = Message)

#allows the user to view the private conversation they are having with the specified user
@app.route('/messages/<username>', methods = ['GET', 'POST'])
@login_required
def messages(username):
    msg_to = User.query.filter_by(username = username).first_or_404()
    if msg_to.id == 1 or msg_to == current_user: #Prevent chatting with admin or self
        return render_template('admin_restricted.html')
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

    messages = current_user.msgs_btw(username).paginate(page, app.config['MESSAGES_PER_PAGE'], False)

    for message in messages.items:
        if message.author != current_user:
            message.seen = 1    
    db.session.commit()

    next_url = url_for('messages', username = username, page = messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages', username = username, page = messages.prev_num) \
        if messages.has_prev else None

    return render_template('messages.html', title = 'Messages', messages = messages.items, 
                            form0 = form0, form = form, user = msg_to, badge_colour=badge_colour,
                            prev_url = prev_url, next_url = next_url)
