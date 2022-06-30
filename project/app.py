import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_mail import Mail

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import bs4 as bs
import urllib.request
from urllib.request import Request, urlopen
import requests
import os,io,time,ssl

context = ssl.SSLContext()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

app = Flask(__name__)
app.config['SECRET_KEY'] = ''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] =587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_DEFAULT_SENDER'] = ''

db.init_app(app)
data_url =r"https://res.cloudinary.com/kishanmodi/raw/upload/v1647103420/main_data_kpqadr.csv"
#created a login manager to save session of user
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

#jwt token for reset password
jwt.init_app(app)

#flask_mail for sending reset email
mail.init_app(app)

#imported user model for database
from .models import User

#if database doesn't exists create one
with app.app_context():
  db.create_all()

#load user from cookie if logged in user exists
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


#blueprints auth routes
from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

  #non-auth parts
from .main import main as main_blueprint
app.register_blueprint(main_blueprint)

#github blueprint imported from github.py
from .github import blueprint as github_blueprint
app.register_blueprint(github_blueprint, url_prefix="/login")

#google blueprint imported from google.py
from .google import blueprint as google_blueprint
app.register_blueprint(google_blueprint, url_prefix="/login")


#tmdv api
from tmdbv3api import TMDb
tmdb = TMDb()
tmdb.api_key = ''
from tmdbv3api import Movie


#cosine similarity function (if not created yet)
def create_sim():
    data = pd.read_csv(data_url,sep=",")
    # creating a count matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    # creating a similarity score matrix
    sim = cosine_similarity(count_matrix)
    return data,sim


#recommendation function for movies
def rcmd(m):
    m = m.lower()
    try:
        data.head()
        sim.shape
    except:
        data, sim = create_sim()
    #searching movie name in datasets
    if m not in data['movie_title'].unique():
        return('Sorry! The movie your searched is not in our database. Please check the spelling or try with some other movies')
    else:
        #getting index of movie in datasets
        i = data.loc[data['movie_title']==m].index[0]
        lst = list(enumerate(sim[i]))
        lst = sorted(lst, key = lambda x:x[1] ,reverse=True)
        #getting top 10 most similar movies
        lst = lst[1:11]
        l = []
        #getting movie names of top 10 most similar movies
        for i in range(len(lst)):
            a = lst[i][0]
            l.append(data['movie_title'][a])
        #returning movie names of top 10 most similar movies
        return l

def ListOfGenres(genre_json):
    if genre_json:
        genres = []
        genre_str = ", " 
        for i in range(0,len(genre_json)):
            genres.append(genre_json[i]['name'])
        return genre_str.join(genres)

def date_convert(s):
    MONTHS = ['January', 'February', 'Match', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']
    y = s[:4]
    m = int(s[5:-3])
    d = s[8:]
    month_name = MONTHS[m-1]

    result= month_name + ' ' + d + ' '  + y
    return result

def getOttLink(ott_link):
    req = Request(ott_link, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = bs.BeautifulSoup(webpage,'lxml')
    Class = soup.find_all('li', {'class': 'ott_filter_best_price ott_filter_hd'})
    #get the first link from class list
    link = Class[0].find('a')['href']
    return link

def getMovieProviders(movie_id):
    response = requests.get('https://api.themoviedb.org/3/movie/{}/watch/providers?api_key={}'.format(movie_id,tmdb.api_key))
    country_json = response.json()
    try:
        provider_json=country_json['results']['IN']
        ott_link = provider_json['link']
        try:
            ott_link = getOttLink(ott_link)
        except:
            ott_link=ott_link
        flatrate=provider_json['flatrate']
        provider_name=flatrate[0]['provider_name']
        print(movie_id)
        img=flatrate[0]['logo_path']
        logo = 'https://image.tmdb.org/t/p/original{}'.format(img)
        print(logo)
        return ott_link,logo
    except:
        pass


def getYoutubeTrailer(movie_id):
    response = requests.get('https://api.themoviedb.org/3/movie/{}/videos?api_key={}'.format(movie_id,tmdb.api_key))
    trailer_json = response.json()
    try:
        for i in range(0,7):
            if trailer_json['results'][i]['type']=='Trailer':
                trailer_link = trailer_json['results'][i]['key']
                trailer_link='https://www.youtube.com/embed/{}?vq=hd1080&rel=0&disablekb=1'.format(trailer_link)
                print(trailer_link)
                return trailer_link
            if trailer_json['results'][i]['type']=='Trailer':
                break
    except:
        return None

def MinsToHours(duration):
    if duration%60==0:
        return "{:.0f} hours".format(duration/60)
    else:
        return "{:.0f} hours {} minutes".format(duration/60,duration%60)

def get_suggestions(): 
    data = pd.read_csv(data_url,sep=",")
    return list(data['movie_title'].str.capitalize())


#creating a route for homepage
@app.route("/")
def index():
    suggestions = get_suggestions()
    return render_template('index.html',suggestions=suggestions)

#creating a route for recommendation
@app.route("/recommend")
def recommend():
    import time
    start_time = time.time()
    movie = request.args.get('movie') # get movie name from the URL
    r = rcmd(movie) #calling recommendation function
    movie = movie.lower()
    if type(r)==type('string'): # no such movie found in the database
        suggestions = get_suggestions()
        #returning error message
        return render_template('recommend.html',movie=movie,r=r,t='s',suggestions=suggestions)
    else:
        #tmdb object for movie search
        tmdb_movie = Movie()
        result = tmdb_movie.search(movie)

        # get movie id and movie title
        movie_id = result[0].id
        movie_name = result[0].title

        # making API call
        try:
            ott_link,logo=getMovieProviders(movie_id)
        except:
            logo=""
            ott_link=""
            print("no link")
        youtube_link=getYoutubeTrailer(movie_id)
        print(type(youtube_link))
        if youtube_link==None:
            youtube_link="None"
        response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}'.format(movie_id,tmdb.api_key))
        data_json = response.json() # get json data of movies
        imdb_id = data_json['imdb_id'] # get imdb id of movie
        poster = data_json['poster_path'] # get poster path of movie
        img_path = 'https://image.tmdb.org/t/p/original{}'.format(poster) # get image path of movie

        # getting list of genres form json
        genre = ListOfGenres(data_json['genres']) # get list of genres of movie

        # web scraping to get user reviews from IMDB site
        sauce = urllib.request.urlopen('https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt'.format(imdb_id)).read()
        soup = bs.BeautifulSoup(sauce,'lxml')
        soup_result = soup.find_all("div",{"class":"text show-more__control"}) # get user reviews from IMDB site

        reviews_list = [] # list of reviews
        for reviews in soup_result:
            if reviews.string:
                reviews.string = reviews.string[0:1000]
                reviews_list.append(reviews.string)

        # getting votes with comma as thousands separators
        vote_count = "{:,}".format(result[0].vote_count)

        # convert date to readable format (eg. 10-06-2019 to June 10 2019)
        rd = date_convert(result[0].release_date)

        # getting the status of the movie (released or not)
        status = data_json['status']

        # convert minutes to hours minutes (eg. 148 minutes to 2 hours 28 mins)
        runtime = MinsToHours(data_json['runtime'])

        # getting the posters for the recommended movies
        poster = []
        # movie_title_list = []
        for movie_title in r:
            list_result = tmdb_movie.search(movie_title)
            movie_id = list_result[0].id #get movie id
            response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}'.format(movie_id,tmdb.api_key))
            data_json = response.json() # get json data of movie for poster
            poster.append('https://image.tmdb.org/t/p/original{}'.format(data_json['poster_path']))
        movie_cards = {poster[i]: r[i] for i in range(len(r))} # creating a dictionary of poster and movie title

        # get movie names for auto completion
        suggestions = get_suggestions()
        justwatch=""
        flatrate=""
        img=""
        print("--- %s seconds ---" % (time.time() - start_time))
        return render_template('recommend.html',movie=movie,mtitle=r,t='l',cards=movie_cards,
            result=result[0],reviews=reviews_list,img_path=img_path,genres=genre,vote_count=vote_count,
            release_date=rd,status=status,runtime=runtime,suggestions=suggestions,logo=logo,youtube_link=youtube_link,ott_link=ott_link)

if __name__ == '__main__':
    app.run(debug=True)
