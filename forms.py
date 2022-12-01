from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class CreateKismetForm(FlaskForm):
    username = StringField("Kismet Username", validators=[DataRequired()])
    password = StringField('Kismet Password', validators=[DataRequired()])
    submit = SubmitField('Change Login Info')

