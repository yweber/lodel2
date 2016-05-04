# -*- coding: utf-8 -*-
import os
import datetime
from werkzeug.contrib.sessions import FilesystemSessionStore

from lodel.interface.web.router import get_controller
from lodel.interface.web.lodelrequest import LodelRequest

# TODO Déplacer ces trois paramètres dans les settings
SESSION_FILES_TEMPLATE = 'lodel_%s.sess'
SESSION_FILES_BASE_DIR = 'tmp/sessions'
SESSION_EXPIRATION_LIMIT = 900 # 15 min

session_store = FilesystemSessionStore(path=SESSION_FILES_BASE_DIR, filename_template=SESSION_FILES_TEMPLATE)

# TODO Déplacer cette méthode dans un module Lodel/utils/datetime.py
def get_utc_timestamp():
    d = datetime.datetime.utcnow()
    epoch = datetime.datetime(1970, 1, 1)
    t = (d - epoch).total_seconds()
    return t

# TODO déplacer dans un module "sessions.py"
def delete_old_session_files(timestamp_now):
    session_files_path = os.path.abspath(session_store.path)
    session_files = [file_object for file_object in os.listdir(session_files_path)
                     if os.path.isfile(os.path.join(session_files_path, file_object))]
    for session_file in session_files:
        expiration_timestamp = os.path.join(session_files_path, session_file).st_mtime + \
                                                                                      SESSION_EXPIRATION_LIMIT
        if timestamp_now > expiration_timestamp:
            os.unlink(os.path.join(session_files_path, session_file))


# TODO Déplacer dans une module "sessions.py"
def is_session_file_expired(timestamp_now, sid):
    session_file = session_store.get_session_filename(sid)
    expiration_timestamp = os.stat(session_file).st_mtime + SESSION_EXPIRATION_LIMIT
    if timestamp_now < expiration_timestamp:
        return False
    return True

# WSGI Application
def application(env, start_response):
    current_timestamp = get_utc_timestamp()
    delete_old_session_files(current_timestamp)
    request = LodelRequest(env)
    sid = request.cookies.get('sid')
    if sid is None or sid not in session_store.list():
        request.session = session_store.new()
        request.session['last_accessed'] = current_timestamp
    else:
        request.session = session_store.get(sid)
        if is_session_file_expired(current_timestamp, sid):
            session_store.delete(request.session)
            request.session = session_store.new()
            request.session['user_context'] = None
        request.session['last_accessed'] = current_timestamp

    controller = get_controller(request)
    response = controller(request)
    if request.session.should_save:
        session_store.save(request.session)
        response.set_cookie('sid', request.session.sid)

    return response(env, start_response)
