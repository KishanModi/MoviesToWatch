from flask import Flask
from .app import app

#api keys here they must be hidden

app.config["GITHUB_OAUTH_CLIENT_ID"]=''
app.config["GITHUB_OAUTH_CLIENT_SECRET"]=''
app.config["GOOGLE_OAUTH_CLIENT_ID"]=""
app.config["GOOGLE_OAUTH_CLIENT_SECRET"]=""
