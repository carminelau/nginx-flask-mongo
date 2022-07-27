@application.route("/punti_percorso_centralina", methods=["POST"]) #da modificare con application.route
def punti_centralina():
    token = request.form.get("token", None)
    apikey = request.form.get("apikey", None)
    pagina = max(int(request.form.get("pagina", 1)), 1) 
    elementi = int(request.form.get("elementi", 1)) 
    limite = min(4, max(1, round(elementi/25)))
    if token != None:
        response = json.loads(check_token_user(token).response[0].decode('utf-8'))
    else:
        response = json.loads(check_apikey(apikey).response[0].decode('utf-8'))
    if response["response_code"]==200:
        centralina = request.form["ID"]
        date_str = request.form["date"]
        date = date_str.split("-")
        timestamp = datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
        res = routes.find_one({"ID": centralina, "timestamp": timestamp, "points": {"$exists": True}}, {"_id": 0, "points": 1})
        

        if res != None:
            if pagina == 1:
                points = res["points"][0:elementi]
            else:
                points = res["points"][(pagina-1)*elementi:pagina*elementi]
            pagine_totali = -(len(res["points"]) // -(limite*25))
            coordinates = []
            for point in points:
                coordinates.append({"coordinate":point[0],"timestamp":point[1]})
            if len(coordinates) > 0:
                myResponse = {
                    'response_code' : 200,
                    'message' : 'Punti trovati',
                    'result' : coordinates,
                    'pagine_totali': pagine_totali,
                    'pagina_corrente': pagina
                }
            else:
                myResponse = {
                    'response_code' : 400,
                    'message' : 'Punti non trovati',
                    'result' : []
                }

        return jsonify(myResponse)