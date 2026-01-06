from flask import Blueprint, render_template, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError

from app.lib.user import login_required, admin_required, users_enabled_required, logout_user
from app.models import User
from app.forms import UserLoginForm, UserEditForm
from app import db


bp = Blueprint('user', __name__)


@bp.route('/login', methods=['GET', 'POST'])
@users_enabled_required
def login():
    form = UserLoginForm()
    if form.validate_on_submit():
        user = User.login(form.username.data, form.password.data)
        if user:
            flash(f"Welcome back, {user.username}!", 'success')
            return redirect(url_for('index.index'))
        flash("Invalid username or password.", 'danger')
    return render_template('user/login.html.j2', form=form)


@bp.route('/logout', methods=['POST'])
@users_enabled_required
def logout():
    logout_user()
    flash("You are now logged out.", 'info')
    return redirect(url_for('.login'))


@bp.route('/list', methods=['GET'])
@users_enabled_required
@admin_required
def list_users():
    users = User.query.order_by(User.username.asc()).all()
    return render_template('user/list.html.j2', users=users)


@bp.route('/edit/new', methods=['GET', 'POST'])
@bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@users_enabled_required
@admin_required
def edit(user_id=None):
    user = None
    if user_id:
        user = User.query.get(user_id)
        if not user:
            flash("User ID not found.", 'danger')
            return redirect(url_for('.list_users'))

    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user = user or User()
        form.populate_obj(user)
        db.session.add(user)
        try:
            db.session.commit()
            if user_id:
                flash(f"Saved changes to user {user.username}", 'success')
            else:
                flash(f"Created new user {user.username}", 'success')
                return redirect(url_for('.edit', user_id=user.id))
        except IntegrityError:
            db.session.rollback()
            flash("Username is not unique", 'danger')

    return render_template('user/edit.html.j2', user=user, form=form)
