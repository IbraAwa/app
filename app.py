"""Intranet du cartel - atelier cybersecurite. VOLONTAIREMENT VULNERABLE : ne pas exposer sur Internet."""
import base64
import hashlib
import os
import sqlite3

from flask import (Flask, abort, jsonify, make_response, redirect,
                   render_template_string, request, session, url_for)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "atelier-cartel-2026")
DB_PATH = os.environ.get("DB_PATH", "cartel.db")
RESET_TOKEN = os.environ.get("RESET_TOKEN", "prof")

CHEF_PASSWORD = "cobraNoir1978"   # animal + adjectif + annee : a retrouver par wordlist
CODE_ACCES = "ALPHA-7731"         # transmis dans l'en-tete reseau X-Code-Acces
FLAG_SQLI = "FLAG{sqli_union_ok}"
FLAG_HASH = "FLAG{hash_cracked_ok}"
FLAG_ROUTES = "FLAG{hidden_routes_ok}"
FLAG_PIN = "FLAG{pin_brute_force_ok}"
FLAG_API = "FLAG{api_chain_ok}"
# Flag etape 1 (PIN) : dans le ZIP, pas dans l'application.


def md5(text):
    return hashlib.md5(text.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        DROP TABLE IF EXISTS members;
        DROP TABLE IF EXISTS missions;
        DROP TABLE IF EXISTS dossiers;
        CREATE TABLE members (id INTEGER PRIMARY KEY, username TEXT, password TEXT,
                              role TEXT, animal TEXT, birth_year INTEGER);
        CREATE TABLE missions (id INTEGER PRIMARY KEY, name TEXT, description TEXT);
        CREATE TABLE dossiers (id INTEGER PRIMARY KEY, owner_id INTEGER, titre TEXT, contenu TEXT);
    """)
    conn.executemany("INSERT INTO members VALUES (?, ?, ?, ?, ?, ?)", [
        (1, "recrue_04", md5("recrue2026"), "recrue", "hibou", 2001),
        (2, "el_jefe", md5(CHEF_PASSWORD), "chef", "cobra", 1978),
        (3, "sys_audit", FLAG_SQLI, "systeme", "-", 1900),
    ])
    conn.executemany("INSERT INTO missions VALUES (?, ?, ?)", [
        (1, "Surveillance du port", "Suivi des cargaisons a Culiacan"),
        (2, "Infiltration Sinaloa", "Acces au reseau interne du cartel"),
        (3, "Operation El Jefe", "Mission classifiee"),
    ])
    conn.executemany("INSERT INTO dossiers VALUES (?, ?, ?, ?)", [
        (1, 1, "Note de recrue", "Rien a signaler."),
        (2, 2, "Dossier du chef", "Agenda et contacts du chef. Confidentiel."),
        (3, 2, "OPERATION FINALE", "Recette : gâteau au chocolat pour ma dulciné. Ingrédients : 200 g de chocolat noir, 150 g de beurre, 4 oeufs, 150 g de sucre, 80 g de farine, 1 cuillère à café de levure. Préparation : faire fondre le chocolat et le beurre. Fouetter les oeufs avec le sucre, ajouter le mélange chocolat, puis la farine et la levure. Cuire 25 minutes à 180 degrés."),
    ])
    conn.commit()
    conn.close()


def run_query(sql):
    """Execute du SQL brut (volontairement non parametre) et renvoie (lignes, erreur)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(sql).fetchall(), None
    except sqlite3.Error as exc:
        return [], str(exc)
    finally:
        conn.close()


BASE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="robots" content="noindex,nofollow">
<title>Cartel - {{ title }}</title>
<style>
body{font-family:system-ui,sans-serif;background:#111;color:#ddd;margin:2rem;max-width:900px}
input,button{padding:.4rem;margin:.2rem}
table{border-collapse:collapse;margin-top:1rem}
td{border:1px solid #444;padding:.3rem .6rem}
.err{color:#f66}.flag{color:#6f6;font-weight:bold;font-size:1.2rem}
</style></head><body>
<h1>Intranet du cartel</h1>
<nav>{% if session.get('user') %}<a href="/recherche">Recherche</a> | <a href="/compte">Mon compte</a> | <a href="/logout">Deconnexion</a>{% else %}<a href="/login">Connexion</a>{% endif %}</nav>
<hr>
{{ content|safe }}
</body></html>"""

LOGIN_TPL = """<h2>Connexion</h2>
<form method="post">
<input name="username" placeholder="identifiant"><br>
<input name="password" type="password" placeholder="mot de passe"><br>
<button>Se connecter</button>
</form>
{% if error %}<p class="err">{{ error }}</p>{% endif %}"""

SEARCH_TPL = """<h2>Recherche de missions</h2>
<form><input name="q" value="{{ q }}"><button>Chercher</button></form>
{% if err %}<p class="err">{{ err }}</p>{% endif %}
{% if rows %}<table>{% for r in rows %}<tr>{% for c in r %}<td>{{ c }}</td>{% endfor %}</tr>{% endfor %}</table>{% endif %}"""

COMPTE_TPL = """<h2>Bienvenue, {{ user }}</h2>
<p>Role : {{ role }}</p>
{% if role == 'chef' %}
<p class="err">Activite suspecte detectee sur ce compte. Zone sensible verrouillee.</p>
<p class="flag">{{ flag_hash }}</p>
{% endif %}
<script>
// TODO retirer avant mise en prod : /chef/salle-secrete
fetch('/api/v1/statut');
fetch('/api/v1/dossiers/2').then(r => r.json()).then(d => console.log(d));
</script>"""

SALLE_TPL = """<h2>Salle sensible</h2>
{% if ok %}
<p class="flag">{{ flag }}</p>
<p>Acces au reseau interne du chef accorde. Poursuivez la mission.</p>
{% else %}
<form method="post"><label>Code d'acces :</label><input name="code"><button>Valider</button></form>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
{% endif %}"""


def page(title, tpl, **ctx):
    content = render_template_string(tpl, **ctx)
    return render_template_string(BASE, title=title, content=content)


MISSION1_TPL = """<h2>Mission 1 : le coffre</h2>
<p>Le cartel a laisse un coffre chiffre. Telechargez-le, trouvez son PIN a 4 chiffres
avec un script Python, puis ouvrez-le. Le fichier contient l'adresse de l'intranet et le flag.</p>
<p><a href="/static/coffre.zip">Telecharger coffre.zip</a></p>
<form method="post" action="/mission/1">
<input name="flag" placeholder="FLAG{...}"><button>Valider le flag</button>
</form>
{% if msg %}<p class="{{ cls }}">{{ msg }}</p>{% endif %}
<p><a href="/login">Aller a l'intranet (etape 2)</a></p>"""


@app.route("/")
def index():
    return redirect(url_for("mission1"))


@app.route("/mission/1", methods=["GET", "POST"])
def mission1():
    msg, cls = None, "err"
    if request.method == "POST":
        if request.form.get("flag", "").strip() == FLAG_PIN:
            msg, cls = "Flag valide : etape 1 reussie. Passez a l'intranet.", "flag"
        else:
            msg = "Flag incorrect."
    return page("Mission 1", MISSION1_TPL, msg=msg, cls=cls)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        query = ("SELECT id, username, role FROM members "
                 f"WHERE username = '{username}' AND password = '{md5(password)}' "
                 "ORDER BY id LIMIT 1")
        rows, err = run_query(query)
        if err:
            error = f"Erreur SQL : {err}"
        elif rows:
            session["uid"], session["user"], session["role"] = rows[0]
            return redirect(url_for("compte"))
        else:
            error = "Identifiants invalides."
    return page("Connexion", LOGIN_TPL, error=error)


@app.route("/recherche")
def recherche():
    if "user" not in session:
        return redirect(url_for("login"))
    q = request.args.get("q", "")
    rows, err = [], None
    if q:
        rows, err = run_query(f"SELECT name, description FROM missions WHERE name LIKE '%{q}%'")
    return page("Recherche", SEARCH_TPL, q=q, rows=rows, err=err)


@app.route("/compte")
def compte():
    if "user" not in session:
        return redirect(url_for("login"))
    return page("Mon compte", COMPTE_TPL, user=session["user"], role=session["role"],
                flag_hash=FLAG_HASH)


@app.route("/api/v1/statut")
def statut():
    if "user" not in session:
        abort(401)
    resp = make_response(jsonify(user=session["user"], role=session["role"]))
    if session.get("role") == "chef":
        resp.headers["X-Code-Acces"] = CODE_ACCES
    return resp


@app.route("/api/v1/dossiers/<int:dossier_id>")
def dossier(dossier_id):
    if "user" not in session:
        abort(401)
    # Faille IDOR volontaire : aucun controle que le dossier appartient a l'utilisateur.
    rows, _ = run_query(f"SELECT id, owner_id, titre, contenu FROM dossiers WHERE id = {dossier_id}")
    if not rows:
        abort(404)
    d = rows[0]
    payload = dict(id=d[0], owner_id=d[1], titre=d[2], contenu=d[3])
    if dossier_id == 3:
        payload["operation"] = "Faire plaisir à ma dulciné"
        payload["deroule"] = ("Date : fin 2027, 14h00. Achat des ingrédients figurant dans la liste "
                              "de la page précédente, par les membres du cartel. Aucun vol d'ingrédient.")
    resp = make_response(jsonify(**payload))
    if dossier_id == 3:
        resp.headers["X-Mission-Trace"] = base64.b64encode(FLAG_API.encode()).decode()
    return resp


@app.route("/chef/salle-secrete", methods=["GET", "POST"])
def salle():
    if session.get("role") != "chef":
        abort(404)
    ok, error = False, None
    if request.method == "POST":
        if request.form.get("code", "").strip().upper() == CODE_ACCES:
            ok = True
        else:
            error = "Code incorrect."
    return page("Salle sensible", SALLE_TPL, ok=ok, error=error, flag=FLAG_ROUTES)


@app.route("/robots.txt")
def robots():
    resp = make_response("User-agent: *\nDisallow: /chef/salle-secrete\n")
    resp.mimetype = "text/plain"
    return resp


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/reset")
def reset():
    if request.args.get("token") != RESET_TOKEN:
        abort(403)
    init_db()
    session.clear()
    return "Base reinitialisee."


init_db()
