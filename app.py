from flask import Flask, render_template, request, jsonify
import requests
import json
import time  # Importamos la librería time para medir el tiempo de ejecución

app = Flask(__name__)
apikey = '320cbc85'

def searchfilms(search_text, page="1"):
    start_time = time.time()  # Marca el tiempo de inicio
    url = "https://www.omdbapi.com/?s=" + search_text + "&apikey=" + apikey + "&page=" + page
    response = requests.get(url)

    end_time = time.time()  # Marca el tiempo de finalización
    execution_time = end_time - start_time  # Calcula el tiempo transcurrido
    print(f"searchfilms API call took {execution_time:.4f} seconds.")  # Imprime el tiempo de ejecución

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve search results.")
        return None

def getmoviedetails(movie):
    start_time = time.time()  # Marca el tiempo de inicio
    url = "https://www.omdbapi.com/?i=" + movie["imdbID"] + "&apikey=" + apikey
    response = requests.get(url)

    end_time = time.time()  # Marca el tiempo de finalización
    execution_time = end_time - start_time  # Calcula el tiempo transcurrido
    print(f"getmoviedetails API call took {execution_time:.4f} seconds.")  # Imprime el tiempo de ejecución

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve search results.")
        return None

def get_country_flag(fullname):
    start_time = time.time()  # Marca el tiempo de inicio
    url = f"https://restcountries.com/v3.1/name/{fullname}?fullText=true"
    response = requests.get(url)

    end_time = time.time()  # Marca el tiempo de finalización
    execution_time = end_time - start_time  # Calcula el tiempo transcurrido
    print(f"get_country_flag API call took {execution_time:.4f} seconds.")  # Imprime el tiempo de ejecución

    if response.status_code == 200:
        country_data = response.json()
        if country_data:
            return country_data[0].get("flags", {}).get("svg", None)
    print(f"Failed to retrieve flag for country code: {fullname}")
    return None

def merge_data_with_flags(filter):
    start_time = time.time()  # Marca el tiempo de inicio
    filmssearch1 = searchfilms(filter, "1")
    filmssearch2 = searchfilms(filter, "2")
    combined_filmssearch =filmssearch1["Search"] + filmssearch2["Search"] #mezcla las dos primeras paginas de resultados
    unique_filmssearch = [] #en caso de haber peliculas repetidas se filtran
    for i in combined_filmssearch:
        if i not in unique_filmssearch:
            unique_filmssearch.append(i)

    known_countries = {}
    moviesdetailswithflags = []
    
    print("COMBINED FILMSEARCH",combined_filmssearch) #logs
    print("unique FILMSEARCH",unique_filmssearch)
    
    contador_country = 0
    contador_unique_country = 0
    for movie in unique_filmssearch:
        moviedetails = getmoviedetails(movie)
        countriesNames = moviedetails["Country"].split(",")
        countries = []
        
        for country in countriesNames:
            contador_country += 1 #logs
            if country not in known_countries: #si es que no se encuentra en los paises que ya han sido llamados por la api, se llaman y almacenan
                contador_unique_country += 1 #logs
                countrywithflag = {
                    "name": country.strip(),
                    "flag": get_country_flag(country.strip())
                }
                known_countries[country] = countrywithflag
            countries.append(known_countries[country]) # si es que ya ha sido llamado se utiliza el valor del diccionario almacendo

        moviewithflags = {
            "title": moviedetails["Title"],
            "year": moviedetails["Year"],
            "countries": countries
        }
        moviesdetailswithflags.append(moviewithflags)
    print("conatdor countries ",contador_country)
    print("contador unique countries", contador_unique_country) #logs
    print(moviesdetailswithflags)

    end_time = time.time()  # Marca el tiempo de finalización
    execution_time = end_time - start_time  # Calcula el tiempo transcurrido
    print(f"merge_data_with_flags function took {execution_time:.4f} seconds.")  # Imprime el tiempo de ejecución
    return moviesdetailswithflags

@app.route("/")
def index():
    filter = request.args.get("filter", "").upper()
    return render_template("index.html", movies=merge_data_with_flags(filter))

@app.route("/api/movies")
def api_movies():
    filter = request.args.get("filter", "")
    return jsonify(merge_data_with_flags(filter))

if __name__ == "__main__":
    app.run(debug=True)

