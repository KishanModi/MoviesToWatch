from flask import Flask
from .app import app

#api keys here they must be hidden

app.config["GITHUB_OAUTH_CLIENT_ID"]='073fe3e810fe77ddaff5'
app.config["GITHUB_OAUTH_CLIENT_SECRET"]='6a16c3bad272503ad40640d85d6228b7236f7b1a'
app.config["GOOGLE_OAUTH_CLIENT_ID"]="988725132346-qcglec925m70br1t4onhm61shlmn2u30.apps.googleusercontent.com"
app.config["GOOGLE_OAUTH_CLIENT_SECRET"]="gXE3DRKX879RhiraAwILgAfX"