from flask import render_template, flash, redirect, request, url_for, json, jsonify, Response
from flask import send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from time import time
from random import randrange
import subprocess, os
from app.models import User, Post, Server, Activation
from app.models import FacterVersion, FacterMacaddress, FacterArchitecture, FacterVirtual, FacterType
from app.models import FacterManufacturer, FacterProductname, FacterProcessor, FacterFacts, Sshkey
from app import app, db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ActivatePinForm
from app.forms import ResetPasswordRequestForm, ResetPasswordForm, ChangePasswordForm
from app.forms import DeleteServerForm
from app.lib import get_one_or_create, gen_ssh_key_pair
import logging

HTTP_204_NO_CONTENT = 204

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
            if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
            if posts.has_prev else None

    return render_template('index.html', title='Home Page', form=form,
            posts=posts.items, next_url=next_url, prev_url=prev_url)

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

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)

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

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
            if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
            if posts.has_prev else None

    return render_template('user.html', user=user, posts=posts.items,
            next_url=next_url, prev_url=prev_url)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))

    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))

    current_user.follow(user)
    db.session.commit()
    flash('You are following {}'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))

    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))

    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
            if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
            if posts.has_prev else None

    return render_template('index.html', title='Explore',
        posts=posts.items, next_url=next_url, prev_url=prev_url)

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
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Your current password is wrong.')
            return redirect(url_for('change_password'))

        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been changed.')
        return redirect(url_for('edit_profile'))

    return render_template('change_password.html', form=form)

@app.route('/installation_keys')
@login_required
def installation_keys():
    expire_hours = int(app.config['JWT_INSTALLATION_KEY_EXPIRES'] / 3600)
    return render_template('installation_keys.html', title='Installation Keys',
            expire_hours=expire_hours)

@app.route('/download_installation_key')
@login_required
def download_installation_key():
    expires = int(time() + app.config['JWT_INSTALLATION_KEY_EXPIRES'])
    filename = 'iWe-install-key-' + current_user.username + '-' + \
            str(expires) + '.json'
    access_token = {
            'installation_key': current_user.get_installation_key_token(),
            'request_activation_url': url_for('request_activation_pin', _external=True)
            }

    body = 'Downloaded installation key '+ current_user.username + '-' + str(expires)
    post = Post(body=body, author=current_user)
    db.session.add(post)
    db.session.commit()
    flash(body)

    return Response(json.dumps(access_token), mimetype='application/json',
            headers={'Content-Disposition':'attachment;filename=' + filename})

def create_it_all(user, facter_json, session):
    #TODO check these created status
    (facterversion, created) = get_one_or_create(session, FacterVersion, facterversion = facter_json['facterversion'])
    (architecture, created) = get_one_or_create(session, FacterArchitecture, architecture = facter_json['architecture'])
    (virtual, created) = get_one_or_create(session, FacterVirtual, virtual = facter_json['virtual'])
    (ftype, created) = get_one_or_create(session, FacterType, type = facter_json['type'])
    (manufacturer, created) = get_one_or_create(session, FacterManufacturer, manufacturer = facter_json['manufacturer'])
    (productname, created) = get_one_or_create(session, FacterProductname, productname = facter_json['productname'])
    (processor0, created) = get_one_or_create(session, FacterProcessor, processor0 = facter_json['processor0'])

    (macaddress, created) = get_one_or_create(session, FacterMacaddress, macaddress = facter_json['macaddress'])

    facts = FacterFacts(
            is_virtual = facter_json['is_virtual'],
            serialnumber = facter_json['serialnumber'],
            uuid = facter_json['uuid'],
            physicalprocessorcount = facter_json['physicalprocessorcount'],
            processorcount = facter_json['processorcount'],
            memorysize = facter_json['memorysize'],
            memorysize_mb = facter_json['memorysize_mb'],
            blockdevice_sda_size = facter_json['blockdevice_sda_size'],

            facterversion_id = facterversion.id,
            architecture_id = architecture.id,
            virtual_id = virtual.id,
            type_id = ftype.id,
            manufacturer_id = manufacturer.id,
            productname_id = productname.id,
            processor_id = processor0.id,
            facter_json = json.dumps(facter_json))

    facts.add_macaddress(macaddress)

    db.session.add(facts)
    db.session.commit()

    server = Server(owner=user, facter_facts_id=facts.id)
    db.session.add(server)
    db.session.commit()

    activation = Activation(server_id=server.id, user_id=user.id, activation_pin=randrange(1000, 9999))
    db.session.add(activation)
    db.session.commit()

    return (activation, facts, server)

@app.route('/request_activation_pin', methods=['GET', 'POST'])
def request_activation_pin():
    if current_user.is_authenticated:
        return render_template('404.html'), 404

    installation_key = request.headers.get('installation_key')
    if not installation_key:
        return render_template('404.html'), 404

    user = User.verify_installation_key_token(installation_key)
    if not user:
        return render_template('404.html'), 404

    try:
        facter_json = request.get_json()
    except:
        return render_template('404.html'), 404

    try:
        json.dumps(facter_json)
    except:
        return render_template('404.html'), 404
    if not facter_json:
        return render_template('404.html'), 404

    #TODO: Add mac address
    try:
        facts = FacterFacts.query.filter(
                FacterFacts.is_virtual == facter_json['is_virtual'],
                FacterFacts.serialnumber == facter_json['serialnumber'],
                FacterFacts.uuid == facter_json['uuid'],
                FacterFacts.physicalprocessorcount == facter_json['physicalprocessorcount'],
                FacterFacts.processorcount == facter_json['processorcount'],
                FacterFacts.memorysize == facter_json['memorysize'],
                FacterFacts.memorysize_mb == facter_json['memorysize_mb'],
                FacterFacts.blockdevice_sda_size == facter_json['blockdevice_sda_size'],
                ).first()
    except:
        error = {'error': 'The data we got is not right. Are you using the latest version of the installer?'}
        return Response(json.dumps(error), mimetype='application/json')

    if facts:
        server = Server.query.filter_by(facter_facts_id = facts.id).first()
        if user.id == server.user_id:
            error = {'error': 'This server is already active, delete it before continuing:{}'.format(
                        url_for('server', uuid=server.uuid, _external=True))}
        else:
            error = {'error': 'Something is wrong. If this server was activated in the past, deactivate it before continuing.'}
        return Response(json.dumps(error), mimetype='application/json')

    activation, facts, server = create_it_all(user, facter_json, db.session)

#    server = Server(owner=user, facter_json=facter_json)
#    db.session.add(server)
#    db.session.commit()

#    activation = Activation(server_id=server.id, user_id=user.id, activation_pin=randrange(1000, 9999))
#    db.session.add(activation)
#    db.session.commit()

    filename='download_keys_url.json'
    download_keys_url = url_for('download_server_keys', activation_pin=activation.activation_pin, _external=True)
    activate_pin_url = url_for('activate_pin', activation_pin=activation.activation_pin, _external=True)
    activation_pin_json = {'activation_pin':activation.activation_pin,\
                           'download_keys_url': download_keys_url,\
                           'activate_pin_url': activate_pin_url}

    body = 'Activation pin {} requested by {}({}): {}'.format(activation.activation_pin,
            facter_json['manufacturer'], facter_json['productname'], facter_json['serialnumber'])
    post = Post(body=body, author=user)
    db.session.add(post)
    db.session.commit()

    return Response(json.dumps(activation_pin_json),
            mimetype='application/json',
            headers={'Content-Disposition':'attachment;filename=' + filename})

@app.route('/download_server_keys/<activation_pin>')
def download_server_keys(activation_pin):
    #TODO: Server can be deleted while waiting for activation. Needs to handle that or the client will wait forever!
    if current_user.is_authenticated:
        return render_template('404.html'), 404

    installation_key = request.headers.get('installation_key')
    if not installation_key:
        return render_template('404.html'), 404

    user = User.verify_installation_key_token(installation_key)
    if not user:
        return render_template('404.html'), 404

    activation = Activation.query.filter_by(user_id = user.id, activation_pin = activation_pin).first()
    if activation == None:
        return render_template('404.html'), 404

    activation.last_ping = datetime.utcnow()
    db.session.commit()

    if activation.active == False:
        return '', HTTP_204_NO_CONTENT

    server = Server.query.filter_by(id = activation.server_id).first()

    cmd = [app.config['EASY_RSA_GEN'], server.uuid]
    pwd = os.path.dirname(os.path.realpath(__file__))
    cwd = '{}/{}'.format(pwd, app.config['EASY_RSA_PATH'])
    ret = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if ret.returncode != 0:
        error = {'error': 'Problem found when creating keys. You may need to delete the server and try again.'}
        print (ret)
        return Response(json.dumps(error), mimetype='application/json')

    keys_json = json.loads(ret.stdout)

    pub, priv = gen_ssh_key_pair()
    if not pub or not priv:
        error = {'error': 'Problem found when creating keys. You may need to delete the server and try again.'}
        print (ret)
        return Response(json.dumps(error), mimetype='application/json')

    ssh_key = Sshkey(pub=pub, priv=priv)
    db.session.add(ssh_key)
    db.session.commit()

    server.sshkey_id = ssh_key.id
    db.session.add(ssh_key)
    db.session.commit()
    
    with open(app.config['VPN_CLIENT_CONFIG'], 'r') as vpn_client_conf_file:
        vpn_client_conf = vpn_client_conf_file.read()

    with open(app.config['VPN_CA_CRT'], 'r') as vpn_ca_crt_file:
        vpn_ca_crt = vpn_ca_crt_file.read()

    with open(app.config['VPN_TA_KEY'], 'r') as vpn_ta_key_file:
        vpn_ta_key = vpn_ta_key_file.read()

    filename='client_conf.json'
    client_conf={
          'vpn_client_pvt_key': keys_json['vpn_client_pvt_key'],
          'vpn_client_crt': keys_json['vpn_client_crt'],
          'vpn_ca_crt': vpn_ca_crt,
          'vpn_ta_key': vpn_ta_key,
          'vpn_client_conf': vpn_client_conf,
          'ssh_pub': ssh_key.pub }

    return Response(json.dumps(client_conf),
            mimetype='application/json',
            headers={'Content-Disposition':'attachment;filename=' + filename})

def cleanup_activation_pins(user, older_than_hours):
    current_time = datetime.utcnow()
    time_delta = current_time - timedelta(hours=older_than_hours)
    
    count = Activation.query.filter(Activation.user_id == user.id, Activation.created < time_delta).count()
    if count > 0:
        Activation.query.filter(Activation.user_id == user.id, Activation.created < time_delta).delete()
        db.session.commit()

        body = 'Purged {} old activations'.format(count)
        post = Post(body=body, author=user)
        db.session.add(post)
        db.session.commit()

@app.context_processor
def utility_processor():
    def inject_datetime_delta(datetime_obj):

        seconds = (datetime.utcnow() - datetime_obj).total_seconds()

        if seconds < 120:
            minutes_str = 'now'
        else:
            minutes_str = '{} minutes'.format(int(seconds / 60))

        if seconds < 60 * 60:
            hours_str = '1 hour'
        else:
            hours_str = '{} hours'.format(int(seconds / 60 / 60))

        if seconds / 60 <= 60 :
            time_ago_str = minutes_str
        else:
            time_ago_str = hours_str
        return {'time_ago_str': time_ago_str}
    return dict(inject_datetime_delta=inject_datetime_delta)

@app.route('/list_activation_pins/')
@login_required
def list_activation_pins():
    
    cleanup_activation_pins(current_user, 48)

    page = request.args.get('page', 1, type=int)

    activations = current_user.get_activations().paginate(
            page, app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('list_activation_pins', page=activations.next_num) \
            if activations.has_next else None
    prev_url = url_for('list_activation_pins', page=activations.prev_num) \
            if activations.has_prev else None

    return render_template('list_activation_pins.html', title='List of Activation Pins',
            activations=activations.items, next_url=next_url, prev_url=prev_url)

@app.route('/activate_pin/<activation_pin>', methods=['GET', 'POST'])
@login_required
def activate_pin(activation_pin):
    activation = Activation.query.filter_by(user_id = current_user.id, activation_pin = activation_pin).first()
    if not activation:
        flash('Invalid Pin')
        return redirect(url_for('list_activation_pins'))

    if activation.active:
        flash('Pin is already active')
        return redirect(url_for('list_activation_pins'))

    form = ActivatePinForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash('Wrong password.')
            return redirect(url_for('activate_pin', activation_pin=activation_pin))

        if form.pin.data != activation_pin:
            flash('Wrong pin.')
            return redirect(url_for('activate_pin', activation_pin=activation_pin))

        activation.active = True
        db.session.commit()
        flash('Pin {} is now active'.format(activation_pin))

        body = 'Pin {} activated'.format(activation.activation_pin)
        post = Post(body=body, author=current_user)
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('list_activation_pins'))

    elif request.method == 'GET':
        return render_template('activate_pin.html', title='Activate Your Server', form=form,
                activations=[activation,])
    else:
        flash('Password or pin invalid.')
        return redirect(url_for('activate_pin', activation_pin=activation_pin))

@app.route('/list_servers/')
@login_required
def list_servers():
    page = request.args.get('page', 1, type=int)

    servers = current_user.get_server_list().paginate(
            page, app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('list_servers', page=servers.next_num) \
            if servers.has_next else None
    prev_url = url_for('list_servers', page=servers.prev_num) \
            if servers.has_prev else None

    return render_template('list_servers.html', title='List of your servers',
            servers=servers.items, next_url=next_url, prev_url=prev_url)

@app.route('/server/<uuid>')
@login_required
def server(uuid):
    server = current_user.get_server(uuid)

    if not server:
        flash('Invalid Server')
        return redirect(url_for('list_servers'))

    facter = json.dumps(json.loads(server.get_facts().facter_json), sort_keys = True, indent = 4,
            separators = (',', ': '))

    return render_template('server.html', title='Your server',
            servers=[server,], facter=facter)

    form = ActivatePinForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash('Wrong password.')
            return redirect(url_for('activate_pin', activation_pin=activation_pin))

        if form.pin.data != activation_pin:
            flash('Wrong pin.')
            return redirect(url_for('activate_pin', activation_pin=activation_pin))

        activation.active = True
        db.session.commit()
        flash('Pin {} is now active'.format(activation_pin))

        body = 'Pin {} activated'.format(activation.activation_pin)
        post = Post(body=body, author=current_user)
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('list_activation_pins'))

    elif request.method == 'GET':
        return render_template('activate_pin.html', title='Activate Your Server', form=form,
                activations=[activation,])
    else:
        flash('Password or pin invalid.')
        return redirect(url_for('activate_pin', activation_pin=activation_pin))

@app.route('/delete_server/<uuid>', methods=['GET', 'POST'])
@login_required
def delete_server(uuid):
    server = current_user.get_server(uuid)

    if not server:
        flash('Invalid Server')
        return redirect(url_for('list_servers'))

    facts = server.get_facts()
    facter = json.dumps(json.loads(server.get_facts().facter_json), sort_keys = True, indent = 4,
            separators = (',', ': '))

    form = DeleteServerForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash('Wrong password.')
            return redirect(url_for('delete_server', uuid=uuid))

        if form.serialnumber.data != facts.serialnumber:
            flash('Wrong serial number.')
            return redirect(url_for('delete_server', uuid=uuid))

        if form.macaddress.data.lower() != facts.get_macaddress().lower():
            flash('Wrong MAC address.')
            return redirect(url_for('delete_server', uuid=uuid))

        if current_user.delete_server(uuid) == False:
            flash('Could not delete server.')
            return redirect(url_for('delete_server', uuid=uuid))

        body = 'Server with serialnumber {} and MAC address {} deleted'.format(facts.serialnumber, facts.get_macaddress())
        flash(body)
        post = Post(body=body, author=current_user)
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('list_servers'))

    elif request.method == 'GET':
        return render_template('delete_server.html', title='Delete Your Server', form=form,
                servers=[server,])
    else:
        flash('Password, serial or MAC address are invalid.')
        return redirect(url_for('delete_server', uuid=uuid))
