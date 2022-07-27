#!/usr/bin/env python
import os
import sys
from databases import status,errors,data_tool,routes
from flask import Flask,request,jsonify
import datetime
import json
import geojson


app = Flask(__name__)


@app.route("/")
def hello():
    version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    message = "Hello World from Flask in a Docker container running Python {} with Meinheld and Gunicorn (default)".format(
        version
    )
    return message

@app.route("/inserisci_status_processi", methods = ["POST"])
def inserisci_status_processi():
    dato={}
    err={}
    apikey = request.form["apikey"]
    if(apikey!=""):

        dato["processo"] = request.form["processo"]
        dato["timestamp"] = datetime.datetime.strptime(request.form["timestamp"], "%Y-%m-%d %H:%M").replace(second=0,microsecond=0)
        oldlast= status.find_one({'processo': dato['processo'],'last':True})
        if(oldlast!=None):
            if(oldlast['timestamp'] < dato['timestamp']):
                dato['last'] = True
                try:
                    status.update_one({'processo': dato['processo'], 'last': True}, {'$unset': { 'last': "" }})
                except:
                    print('errore find e update')
        else:
            dato['last'] = True

        dato["delta"]= int(request.form["delta"])
        dato["status"]= int(request.form["status"])

        if (dato["status"]==500):
            err["traceback"]= request.form.get("traceback", "no")
            if(err['traceback']!="no"):
                err["processo"] = dato["processo"]
                err["timestamp"] = datetime.datetime.strptime(request.form["timestamp"], "%Y-%m-%d %H:%M").replace(second=0,microsecond=0)
                try:
                    errors.insert_one(err)
                except:
                    return jsonify({"error": "errore di " + dato["processo"] + " non inserito"})
        try:
            status.insert_one(dato)
        except:
            return jsonify({"error": "status di " + dato["processo"] + " non inserito"})
    
    return jsonify({"success": "Status inserito con successo"})

@app.route("/get_status_processi", methods = ["POST"])
def get_status_processi():
    array=[]
    query = request.form.get("query","")
    stato = request.form.get("status","ALL")
    pagina = max(int(request.form.get("pagina", 1)), 1)
    elementi = int(request.form.get("elementi", 1))
    limite = min(4, max(1, round(elementi/25)))
    if(query==""):
        processo = request.form.get("processo","")
        if processo != "":
            if(stato=='ALL'):
                result = status.find({'processo': {'$regex': '^' + processo, '$options' : 'i'}},{'_id' : 0, 'last':0}).sort('timestamp',-1).limit(limite*25).skip(limite*(pagina-1)*25) 
                pagine_totali = -(status.count_documents({'processo': {'$regex': '^' + processo, '$options' : 'i'} }) // -(limite*25))
            else:
                stato = int(stato)
                result = status.find({'processo': {'$regex': '^' + processo, '$options' : 'i'}, 'status':stato},{'_id' : 0, 'last':0}).sort('timestamp',-1).limit(limite*25).skip(limite*(pagina-1)*25) 
                pagine_totali = -(status.count_documents({'processo': {'$regex': '^' + processo, '$options' : 'i'} }) // -(limite*25))
        else:
            if(stato=='ALL'):
                result = status.find({'last': True},{'_id' : 0, 'last':0}).sort('timestamp',-1).limit(limite*25).skip(limite*(pagina-1)*25) 
                pagine_totali = -(status.count_documents({'last': True}) // -(limite*25))
            else:
                stato = int(stato)
                result = status.find({'last': True, 'status':stato},{'_id' : 0, 'last':0}).sort('timestamp',-1).limit(limite*25).skip(limite*(pagina-1)*25) 
                pagine_totali = -(status.count_documents({'last': True, 'status':stato}) // -(limite*25))
    else:
        if(stato=='ALL'):
            result = status.find({'processo': {'$regex': '^' + query, '$options' : 'i'},'last':True},{'_id' : 0, 'last':0}).sort('timestamp',-1).limit(limite*25).skip(limite*(pagina-1)*25) 
            pagine_totali = -(status.count_documents({}) // -(limite*25))
        else:
            stato = int(stato)
            result = status.find({'processo': {'$regex': '^' + query, '$options' : 'i'},'last':True,'status':stato},{'_id' : 0, 'last':0}).sort('timestamp',-1).limit(limite*25).skip(limite*(pagina-1)*25) 
            pagine_totali = -(status.count_documents({}) // -(limite*25))

    array=list(result)

    if(len(array)!=0):
        myResponse = {
                        'response_code' : 200, 
                        'message' : 'Status trovati correttamente', 
                        'result' : array,
                        'pagine_totali': pagine_totali,
                        'pagina_corrente': pagina
                    }
    else:
        myResponse = {
                        'response_code' : 400, 
                        'message' : 'Nessun status presente', 
                        'result' : {}
                    }

    return jsonify(myResponse)

@app.route("/get_error_processi", methods = ["POST"])
def get_errore_processi():
    array=[]
    risultato={}
    processo = request.form["processo"]
    timestamp =request.form.get("timestamp","")
    pagina = max(int(request.form.get("pagina", 1)), 1) 
    elementi = int(request.form.get("elementi", 1)) 
    limite = min(4, max(1, round(elementi/25)))
    if (timestamp ==""):
        result = errors.find({'processo': {'$regex': '^' + processo, '$options' : 'i'}},{'_id' : 0, 'traceback':0}).sort('timestamp',-1).limit(limite*25).skip(limite*(pagina-1)*25) 
        pagine_totali = -(errors.count_documents({'processo': {'$regex': '^' + processo, '$options' : 'i'} }) // -(limite*25))
        array=list(result)
        
        if(len(array)>=1):
            myResponse = {
                        'response_code' : 200, 
                        'message' : f'Errori di {processo} trovate correttamente', 
                        'result' : array,
                        'pagine_totali': pagine_totali,
                        'pagina_corrente': pagina
                    }
        else:
            myResponse = {
                            'response_code' : 400, 
                            'message' : f'Nessun errore per il {processo}', 
                            'result' : {}
                        }

    else:
        timestamp= datetime.datetime.strptime(timestamp,"%Y-%m-%d %H:%M").replace(second=0,microsecond=0)
        risultato = errors.find_one({'processo':processo ,'timestamp': timestamp},{'_id' : 0})

        if(risultato!={}):
            myResponse = {
                            'response_code' : 200, 
                            'message' : f'Errori di {processo} trovate correttamente', 
                            'result' : risultato
                        }
        else:
            myResponse = {
                            'response_code' : 400, 
                            'message' : f'Nessun errore di {processo}', 
                            'result' : {}
                        }
    

    return jsonify(myResponse)

@app.route("/grafico_status", methods = ["POST"])
def grafico_status():
    processo = request.form["processo"]
    
    timestamp=[]
    data=[]
    for i in range(7):
        start= (datetime.datetime.now() - datetime.timedelta(days=i)).replace(second=0,microsecond=0,hour=0,minute=0)
        finish = (datetime.datetime.now() - datetime.timedelta(days=i)).replace(second=0,microsecond=0,hour=23,minute=59)
        result = status.find({'processo': processo, 'timestamp':{"$gte": start, "$lt": finish}, 'status': 500})
        if (len(list(result))>0):
            timestamp.append(start.strftime("%Y-%m-%d"))
            data.append(0)
        else:
            result = status.find({'processo': processo, 'timestamp': {"$gte": start, "$lt": finish}, 'status': 200})
            if (len(list(result))>0):
                timestamp.append(start.strftime("%Y-%m-%d"))
                data.append(1)

    if ((len(timestamp) == len(data)) and (len(timestamp)!=0)):
        myResponse = {
                    'response_code' : 200,
                    'message' : f'Gradico di {processo}',
                    'result' : {
                        "timestamp" : timestamp,
                        "data" : data
                    }
                }
    else:
        myResponse = {
                    'response_code' : 400,
                    'message' : f'Nessun status trovato per {processo}',
                    'result' : {}                
                }        

    return jsonify(myResponse)


#setdataTool ( prende in input obbligatorio l'id del widget e un dizionario con i dati e lo inserisco nel db )
@app.route("/setdataTool", methods = ["POST"])
def setdataTool():
    token = request.form.get("token", None)
    apikey = request.form.get("apikey", None)
    # if token != None:
    #     response = json.loads(check_token_user(token).response[0].decode('utf-8'))
    # else:
    #     response = json.loads(check_apikey(apikey).response[0].decode('utf-8'))
    # if response["response_code"]==200:
    id_widget = request.form["id_widget"]
    data = request.form["data"]
    try:
        data = json.loads(data)
        data_tool.update_one({"id_widget": id_widget}, {"$set": data}, upsert=True)
        myResponse = {
                    'response_code' : 200,
                    'message' : f'Dati inseriti correttamente',
                    'result' : {}
                }
    except:
        myResponse = {
                    'response_code' : 400,
                    'message' : f'Nessun dato inserito',
                    'result' : {}
                }

    
    return jsonify(myResponse)


#getdataTool (prende in input obbligatorio l'id del widget e restituisce i dati del widget)
@app.route("/getdataTool", methods = ["POST"])
def getdataTool():
    token = request.form.get("token", None)
    apikey = request.form.get("apikey", None)
    # if token != None:
    #     response = json.loads(check_token_user(token).response[0].decode('utf-8'))
    # else:
    #     response = json.loads(check_apikey(apikey).response[0].decode('utf-8'))
    # if response["response_code"]==200:
    id_widget = request.form["id_widget"]
    result = data_tool.find_one({"id_widget": id_widget})
    if (result!=None):
        myResponse = {
                    'response_code' : 200,
                    'message' : f'Dati trovati correttamente',
                    'result' : result
                }
    else:
        myResponse = {
                    'response_code' : 400,
                    'message' : f'Nessun dato trovato',
                    'result' : {}
                }

    
    return jsonify(myResponse)

@app.route("/percorso_centralina", methods=["POST"]) #da modificare con application.route
def percorso_centralina():
    token = request.form.get("token", None)
    apikey = request.form.get("apikey", None)
    # if token != None:
    #     response = json.loads(check_token_user(token).response[0].decode('utf-8'))
    # else:
    #     response = json.loads(check_apikey(apikey).response[0].decode('utf-8'))
    # if response["response_code"]==200:
    if True:
        centralina = request.form["ID"]
        date_str = request.form["date"]
        date = date_str.split("-")
        timestamp = datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
        res = routes.find_one({"ID": centralina, "timestamp": timestamp, "points": {"$exists": True}}, {"_id": 0, "points": 1})
        if res != None:
            points = res["points"]
            coordinates = []
            features = []
            for point in points:
                coordinates.append(point[0])
            line = geojson.Feature(geometry=geojson.LineString(coordinates))
            features.append(line)
            geo = geojson.FeatureCollection(features)
            myResponse = {
                'response_code' : 200,
                'message' : 'Percorso trovato',
                'result' : geo
            }
        else:
            myResponse = {
                'response_code' : 400,
                'message' : 'Percorso non trovato',
                'result' : ''
            }
    else:
        myResponse = {
            'response_code' : 400,
            'message' : 'Token non valido',
            'result' : ''
        }
    return jsonify(myResponse)

@app.route("/punti_percorso_centralina", methods=["POST"]) #da modificare con application.route
def punti_centralina():
    token = request.form.get("token", None)
    apikey = request.form.get("apikey", None)
    pagina = max(int(request.form.get("pagina", 1)), 1) 
    elementi = int(request.form.get("elementi", 1)) 
    limite = min(4, max(1, round(elementi/25)))
    # if token != None:
    #     response = json.loads(check_token_user(token).response[0].decode('utf-8'))
    # else:
    #     response = json.loads(check_apikey(apikey).response[0].decode('utf-8'))
    # if response["response_code"]==200:
    if True:
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



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)

