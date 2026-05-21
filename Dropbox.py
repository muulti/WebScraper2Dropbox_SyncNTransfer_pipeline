import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper
import urllib.parse


#-------------PRÁCTICA DE LABORATORIO 4 -------------#
#Grupo: Diego Pomares, Jannatul Hossain, Sofía Granja
#Asignatura: Sistemas Web
#Fecha: 15/05/2026
#----------------------------------------------------#

app_key = 'xtkd5lbya3r99dy'       # Rellenar con el App Key de tu app en Dropbox
app_secret = 'hlggtsqsy02rv7m'    # Rellenar con el App Secret de tu app en Dropbox
server_addr = "localhost"
server_port = 8070
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        # Escucha en el puerto 8070 la redirección OAuth del navegador
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # Recibe la redirección 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print(peticion)

        # Buscar en la solicitud el "code" (auth_code)
        primera_linea = peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print("\tauth_code: " + auth_code)

        # Devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response.encode())
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        # ─── PASO 1: Redirigir al usuario a la página de autorización de Dropbox ───
        # https://www.dropbox.com/developers/documentation/http/documentation#authorization
        auth_url = (
            "https://www.dropbox.com/oauth2/authorize"
            "?client_id=" + app_key +
            "&response_type=code"
            "&redirect_uri=" + urllib.parse.quote(redirect_uri, safe='') +
            "&token_access_type=offline"
        )
        print("Abriendo navegador para autorización OAuth:")
        print("\t" + auth_url)
        webbrowser.open(auth_url)

        # ─── PASO 2: Recibir el auth_code en el servidor local ───
        auth_code = self.local_server()
        print("auth_code recibido: " + auth_code)

        # ─── PASO 3: Intercambiar el auth_code por un access_token ───
        # https://www.dropbox.com/developers/documentation/http/documentation#oa2-token
        token_uri = "https://api.dropbox.com/oauth2/token"
        data = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }
        response = requests.post(
            token_uri,
            data=data,
            auth=(app_key, app_secret)
        )
        print("Token response status:", response.status_code)
        print("Token response body:", response.text)

        if response.status_code == 200:
            token_json = response.json()
            self._access_token = token_json['access_token']
            print("Access token obtenido: " + self._access_token)
        else:
            print("Error obteniendo access token:", response.text)

        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-list_folder

        headers = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json',
        }
        # Dropbox API: path "" equivale a la raíz "/"
        path = "" if self._path == "/" else self._path
        body = {
            'path': path,
            'recursive': False,
            'include_media_info': False,
            'include_deleted': False,
            'include_has_explicit_shared_members': False,
        }
        response = requests.post(uri, headers=headers, json=body)
        print("\tStatus code:", response.status_code)

        if response.status_code == 200:
            contenido_json = response.json()
            self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)
        else:
            print("\tError list_folder:", response.text)

    def transfer_file(self, file_path, file_data):
        print("/upload")
        uri = 'https://content.dropboxapi.com/2/files/upload'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-upload

        dropbox_api_arg = json.dumps({
            'path': file_path,
            'mode': 'overwrite',
            'autorename': False,
            'mute': False,
            'strict_conflict': False
        })
        headers = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': dropbox_api_arg,
        }
        response = requests.post(uri, headers=headers, data=file_data)
        print("\tStatus code:", response.status_code)

        if response.status_code == 200:
            result = response.json()
            print("\tFichero subido:", result.get('name', ''))
        else:
            print("\tError upload:", response.text)

    def delete_file(self, file_path):
        print("/delete_file")
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-delete

        headers = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json',
        }
        body = {
            'path': file_path
        }
        response = requests.post(uri, headers=headers, json=body)
        print("\tStatus code:", response.status_code)

        if response.status_code == 200:
            result = response.json()
            print("\tFichero eliminado:", result.get('metadata', {}).get('name', ''))
        else:
            print("\tError delete:", response.text)

    def create_folder(self, path):
        print("/create_folder")
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-create_folder

        headers = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json',
        }
        body = {
            'path': path,
            'autorename': False
        }
        response = requests.post(uri, headers=headers, json=body)
        print("\tStatus code:", response.status_code)

        if response.status_code == 200:
            result = response.json()
            print("\tCarpeta creada:", result.get('metadata', {}).get('name', ''))
        else:
            print("\tError create_folder:", response.text)




#----------------AMPLIACION 20% DE LA NOTA --------------------#

    #Funcion para buscar archivos
    def search(self, palabra):
        print("/search")
        uri = 'https://api.dropboxapi.com/2/files/search_v2'
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
        # Buscamos en todo el Dropbox (path vacío) o en la carpeta actual
        path_busqueda = "" if self._path == "/" else self._path
        data = {
            "match_field_options": {"include_highlights": False},
            "options": {
                "file_status": "active",
                "filename_only": False,
                "max_results": 20,
                "path": path_busqueda
            },
            "query": str(palabra)
        }
        response = requests.post(uri, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            files = []
            for match in result.get("matches", []):
                metadata = match.get("metadata", {}).get("metadata", {})
                files.append(metadata)
            return files
        else:
            print(f"Error en busqueda: {response.status_code} - {response.text}")
            return None

    # Funcion para MOVER Y RENOMBRAR archivos
    def move(self, path_origen, path_destino):
        print("/move (sirve para mover y renombrar)")   #el programa tiene 2 botones move() y rename_file(), y va a mirar a las funciones del archivo  actividad_4.py que hemos creado
        uri = 'https://api.dropboxapi.com/2/files/move_v2'
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "allow_ownership_transfer": False,
            "allow_shared_folder": False,
            "autorename": False,
            "from_path": str(path_origen),
            "to_path": str(path_destino)
        }
        response = requests.post(uri, headers=headers, json=data)
        if response.status_code == 200:
            metadata = response.json().get("metadata", {}).get("metadata", {})
            print(f"Éxito: {metadata.get('name')} -> {metadata.get('path_display')}")
            return metadata
        else:
            print(f"Error al mover/renombrar: {response.status_code} - {response.text}")
            return None

    # Funcion para descargar archivos
    def descargarArchivo(self, dropbox_path, local_path):
        print("/download_file")
        uri = 'https://content.dropboxapi.com/2/files/download'
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Dropbox-API-Arg": json.dumps({"path": dropbox_path})
        }
        response = requests.post(uri, headers=headers, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=4096):
                    f.write(chunk)
            print(f"\tArchivo descargado: {dropbox_path} -> {local_path}")
        else:
            print(f"Error al descargar archivo: {response.status_code} - {response.text}")

