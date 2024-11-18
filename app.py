from flask import Flask, render_template, request, jsonify
import requests
import json
import asyncio
import aiohttp
import sqlite3

app = Flask(__name__)
apikey = "320cbc85"

# Inicializar la base de datos SQLite
def init_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()

    # Crear tabla Movie
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Movie (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            year TEXT NOT NULL
        )
    """)

    # Crear tabla Country
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Country (
            name TEXT PRIMARY KEY,
            flag TEXT
        )
    """)

    # Crear tabla MovieCountry (relación muchos a muchos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MovieCountry (
            movie_id TEXT,
            country_name TEXT,
            PRIMARY KEY (movie_id, country_name),
            FOREIGN KEY (movie_id) REFERENCES Movie(id),
            FOREIGN KEY (country_name) REFERENCES Country(name)
        )
    """)

    conn.commit()
    conn.close()

init_db()  # Inicializa la base de datos al iniciar la aplicación

async def fetch_flag_async(session, nation_name):
    url = f"https://restcountries.com/v3.1/name/{nation_name}?fullText=true"
    async with session.get(url) as response:
        if response.status == 200:
            nation_data = await response.json()
            if nation_data:
                return nation_data[0].get("flags", {}).get("svg", None)
    print(f"Failed to retrieve flag for nation: {nation_name}")
    return None

def search_movies(query, page=1):
    url = f"https://www.omdbapi.com/?s={query}&page={page}&apikey={apikey}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve search results.")
        return None

def fetch_movie_details(movie_data):
    url = f"https://www.omdbapi.com/?i={movie_data['imdbID']}&apikey={apikey}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve movie details.")
        return None

def get_cached_movie(movie_id):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Movie.title, Movie.year, Country.name, Country.flag
        FROM Movie
        JOIN MovieCountry ON Movie.id = MovieCountry.movie_id
        JOIN Country ON MovieCountry.country_name = Country.name
        WHERE Movie.id = ?
    """, (movie_id,))
    result = cursor.fetchall()
    conn.close()

    if result:
        # Reconstruir datos desde la base de datos
        countries = [{"name": row[2], "flag": row[3]} for row in result]
        return {
            "title": result[0][0],
            "year": result[0][1],
            "countries": countries
        }
    return None

async def merge_movie_data_with_flags(filter_query, page=1):
    search_results = search_movies(filter_query, page)
    movies_with_flags = []
    if search_results and "Search" in search_results:
        async with aiohttp.ClientSession() as session:
            for movie_data in search_results["Search"]:
                cached_movie = get_cached_movie(movie_data["imdbID"])
                if cached_movie:
                    movies_with_flags.append(cached_movie)
                    continue

                movie_details = fetch_movie_details(movie_data)
                country_names = movie_details["Country"].split(",")
                countries = []
                
                # Crear tareas asíncronas para cada país
                tasks = [fetch_flag_async(session, country.strip()) for country in country_names]
                flags = await asyncio.gather(*tasks)
                
                # Guardar datos en SQLite
                conn = sqlite3.connect("movies.db")
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO Movie (id, title, year) VALUES (?, ?, ?)",
                               (movie_data["imdbID"], movie_details["Title"], movie_details["Year"]))
                for i, country in enumerate(country_names):
                    cursor.execute("INSERT OR IGNORE INTO Country (name, flag) VALUES (?, ?)",
                                   (country.strip(), flags[i]))
                    cursor.execute("INSERT OR IGNORE INTO MovieCountry (movie_id, country_name) VALUES (?, ?)",
                                   (movie_data["imdbID"], country.strip()))
                conn.commit()
                conn.close()

                # Construir la respuesta
                countries = [{"name": country.strip(), "flag": flags[i]} for i, country in enumerate(country_names)]
                movie_with_flags = {
                    "title": movie_details["Title"],
                    "year": movie_details["Year"],
                    "countries": countries
                }
                movies_with_flags.append(movie_with_flags)
    else:
        print("No se encontraron resultados para esta búsqueda.")
    return movies_with_flags

@app.route("/")
async def index():
    filter_query = request.args.get("filter", "").upper()
    page = int(request.args.get("page", 1))  # Obtener la página de la URL
    movies = await merge_movie_data_with_flags(filter_query, page)
    return render_template("index.html", movies=movies, filter=filter_query, page=page)

@app.route("/api/movies")
async def api_movies():
    filter_query = request.args.get("filter", "")
    page = int(request.args.get("page", 1))
    movies = await merge_movie_data_with_flags(filter_query, page)
    return jsonify(movies)

if __name__ == "__main__":
    app.run(debug=True)
