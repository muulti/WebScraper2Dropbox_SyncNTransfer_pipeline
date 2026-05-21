# -*- coding: UTF-8 -*-
from tkinter import messagebox
import requests
import urllib
from urllib.parse import unquote
from bs4 import BeautifulSoup
import time
import helper

#-------------PRÁCTICA DE LABORATORIO 4 -------------#
#Grupo: Diego Pomares, Jannatul Hossain, Sofía Granja
#Asignatura: Sistemas Web
#Fecha: 15/05/2026
#----------------------------------------------------#

class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, password, event=None):
        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()
        print(f"USER: {username}, PSW: {password}")
        print("##### 1. PETICION #####")
        # GET to obtain the MoodleSession cookie and logintoken from the login page
        respuesta1 = requests.get(
            "https://egela.ehu.eus/login/index.php",
            allow_redirects=False,
            timeout=10
        )
        print(f"GET https://egela.ehu.eus/login/index.php -> {respuesta1.status_code} {respuesta1.reason}")
        if respuesta1.status_code == 200:
            MoodleSessionEgela = respuesta1.headers['Set-Cookie'].split('MoodleSessionegela=')[1].split(';')[0]
            logintoken = respuesta1.text.split('logintoken" value="')[1].split('"')[0]
        else:
            print("Error al obtener MoodleSessionegela y logintoken.")
            popup.destroy()
            messagebox.showinfo("Alert Message", "Login incorrect!")
            return

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 2. PETICION #####")
        # POST with credentials to authenticate
        cabeceras = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': f'MoodleSessionegela={MoodleSessionEgela}'
        }
        cuerpo = {
            'username': username,
            'password': password,
            'logintoken': logintoken
        }
        respuesta2 = requests.request(
            "POST",
            "https://egela.ehu.eus/login/index.php",
            headers=cabeceras,
            data=cuerpo,
            allow_redirects=False
        )
        print(f"POST https://egela.ehu.eus/login/index.php -> {respuesta2.status_code} {respuesta2.reason}")
        if respuesta2.status_code == 303:
            location = respuesta2.headers['Location']
            print(f"Location: {location}")
            # The session cookie from GET 1 remains valid; the POST response
            # does not always issue a new Set-Cookie header.
            if 'Set-Cookie' in respuesta2.headers and 'MoodleSessionegela=' in respuesta2.headers['Set-Cookie']:
                MoodleSessionEgela = respuesta2.headers['Set-Cookie'].split('MoodleSessionegela=')[1].split(';')[0]
                print(f"New MoodleSessionegela: {MoodleSessionEgela}")
            # else: keep the MoodleSessionEgela obtained in request 1
        else:
            print("Error al autenticarse.")
            popup.destroy()
            messagebox.showinfo("Alert Message", "Login incorrect!")
            return

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        # GET to follow the first redirect after login.
        # Moodle may respond with 302 or 303 depending on version/config,
        # so we accept any 3xx redirect status.
        cabeceras = {'Cookie': f'MoodleSessionegela={MoodleSessionEgela}'}
        respuesta3 = requests.get(location, headers=cabeceras, allow_redirects=False, timeout=10)
        print(f"GET {location} -> {respuesta3.status_code} {respuesta3.reason}")
        if 300 <= respuesta3.status_code < 400:
            # Another redirect to follow
            location = respuesta3.headers['Location']
            print(f"Location: {location}")
        elif respuesta3.status_code == 200:
            # Final page served directly — no further redirect needed,
            # skip petition 4 and use this response as the dashboard
            respuesta4 = respuesta3
            location = None
        else:
            print("Error al autenticarse.")
            popup.destroy()
            messagebox.showinfo("Alert Message", "Login incorrect!")
            return

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 4. PETICION #####")
        # GET the final redirect — lands on the Moodle dashboard.
        # We parse it to find the course link (Sistemas Web) and verify login
        # by checking the user profile page.
        if location is not None:
            cabeceras = {'Cookie': f'MoodleSessionegela={MoodleSessionEgela}'}
            respuesta4 = requests.get(location, headers=cabeceras, allow_redirects=False, timeout=10)
            print(f"GET {location} -> {respuesta4.status_code} {respuesta4.reason}")
            print(respuesta4.text)
        else:
            print("(Skipped — dashboard already obtained in petition 3)")

        soup = BeautifulSoup(respuesta4.text, "html.parser")
        links = soup.find_all("a", class_="aalink")

        curso_href = None
        for link in links:
            if link.get_text(strip=True) == "Sistemas Web":
                curso_href = link.get("href")
                break

        # Verify authentication by checking if the user profile page loads correctly
        respuestaAuth = requests.get(
            "https://egela.ehu.eus/user/profile.php",
            headers=cabeceras,
            allow_redirects=False,
            timeout=10
        )
        soup_auth = BeautifulSoup(respuestaAuth.text, "html.parser")
        # A logged-in profile page will contain user-specific content;
        # a failed login redirects back to the login page (status 303)
        print("\n##### 5.LG #####")
        login_ok = respuestaAuth.status_code == 200 and "login" not in respuestaAuth.url
        #print(respuestaAuth.text)

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        if login_ok:
            self._login = 1
            self._cookie = MoodleSessionEgela
            self._curso = curso_href if curso_href else ""
            self._root.destroy()
        else:
            self._login = 0
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### Peticion (Página principal de la asignatura en eGela) #####")
        # GET the course main page using the stored session cookie and course URL
        cabeceras = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': f'MoodleSessionegela={self._cookie}'
        }
        respuesta = requests.get(self._curso, headers=cabeceras, allow_redirects=False, timeout=10)

        print("\n##### Analisis del HTML... #####")
        # Parse the course page to find all section (nav-link) hrefs,
        # then navigate into each section looking for /mod/resource/ links.
        # For each resource, follow it to find the pluginfile PDF download URL.
        soup = BeautifulSoup(respuesta.text, "html.parser")
        enlaces = soup.find_all("a", class_="nav-link")

        # Collect all resource links across every section of the course
        resource_links = []
        for enlace in enlaces:
            e = enlace.get("href", "")
            if e.endswith("start"):
                tema = requests.get(e, headers=cabeceras, allow_redirects=False, timeout=10)
                soup_tema = BeautifulSoup(tema.text, "html.parser")
                links = soup_tema.find_all("a", class_="aalink")
                for link in links:
                    l = link.get("href", "")
                    if "/mod/resource/" in l:
                        resource_links.append(l)

        self._refs = []

        # Guard against empty list before computing the step size
        if not resource_links:
            popup.destroy()
            return self._refs

        progress_step = float(100.0 / len(resource_links))

        for l in resource_links:
            time.sleep(0.5)
            recurso = requests.get(l, headers=cabeceras, allow_redirects=False, timeout=10)
            soup_recurso = BeautifulSoup(recurso.text, "html.parser")
            archivo_link = soup_recurso.find("a", href=lambda x: x and "pluginfile" in x)

            if archivo_link:
                archivo_url = archivo_link["href"]
                if ".pdf" in archivo_url:
                    # Extract a clean filename from the URL
                    nombre_archivo = archivo_url.split("/")[-1].split("?")[0]
                    nombre_archivo = urllib.parse.unquote(nombre_archivo)
                    self._refs.append({
                        'pdf_name': nombre_archivo,
                        'pdf_link': archivo_url
                    })

            progress += progress_step
            progress_var.set(progress)
            progress_bar.update()
            time.sleep(0.1)

        popup.destroy()
        return self._refs

    def get_pdf(self, selection):
        print("\t##### descargando PDF... #####")
        # Look up the entry at the given index in _refs
        ref = self._refs[selection]
        pdf_name = ref['pdf_name']
        pdf_link = ref['pdf_link']

        # Download the PDF using the stored session cookie
        cabeceras = {'Cookie': f'MoodleSessionegela={self._cookie}'}
        respuesta = requests.get(pdf_link, headers=cabeceras, timeout=10)
        pdf_content = respuesta.content   # raw bytes, ready to write to disk

        return pdf_name, pdf_content