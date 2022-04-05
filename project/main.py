from flask import Blueprint, render_template, request
from flask_login import login_required, current_user


main = Blueprint('main', __name__)

# #docs route
# @main.route('/docs')
# def docs():
#   return render_template('aboutus.html')

@main.route('/profile')
@login_required
def profile():
  return render_template('profile.html', name=current_user.username)
