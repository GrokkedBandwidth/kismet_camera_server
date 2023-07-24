from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, regexp

class CreateKismetForm(FlaskForm):
    username = StringField("Kismet Username", validators=[DataRequired()])
    password = StringField('Kismet Password', validators=[DataRequired()])
    submit = SubmitField('Change Login Info')

class AddIgnoreMac(FlaskForm):
    mac = StringField("Input MAC", validators=[regexp('^[A-F0-9]{2}(:[A-F0-9]{2}){5}$')])
    submit = SubmitField('Add to Ignore List')

