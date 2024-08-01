from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

url = "https://api.themoviedb.org/3/search/movie"
get_by_id = "https://api.themoviedb.org/3/movie/"
MOVIE_DB_API_KEY = 'MOVIE_DB_API_KEY'
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
headers = {
    "accept": "application/json",
    "Authorization": "0fe8a55c187514648d3a7ea6ab7fe694"
}


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


# with app.app_context():
#     db.create_all()

# new_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )


# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()
class EditForm(FlaskForm):
    rating = StringField('Your rating out of 10')  # add validators
    review = StringField('Your review')
    submit = SubmitField('Submit')


class AddMovie(FlaskForm):
    title = StringField('Movie Title')
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def update():
    form = EditForm()
    movie_id = request.args.get('id')
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/add', methods=["GET", "POST"])
def add_movie():
    form = AddMovie()
    if form.validate_on_submit():
        movie_name = form.title.data
        response = requests.get(url, params={"api_key": MOVIE_DB_API_KEY, "query": movie_name})
        results = response.json()
        return render_template("select.html", data=results.get("results", []))
    return render_template("add.html", form=form)


@app.route('/find', methods=["GET", "POST"])
def find_movie():
    movie_id = request.args.get('id')
    response = requests.get(get_by_id+movie_id, params={"api_key": MOVIE_DB_API_KEY})
    results = response.json()
    new_movie = Movie(
        title=results['title'],
        year=results["release_date"].split("-")[0],
        description=results['overview'],
        img_url=f'{MOVIE_DB_IMAGE_URL}{results['poster_path']}'
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("update", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
