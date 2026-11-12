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
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Cartel - {{ title }}</title>
<style>
:root{--bg:#0c0a08;--panel:#16110d;--panel2:#1d1711;--red:#b11226;--red-d:#7a0f1c;--gold:#d9b24a;--bone:#ece4d2;--mute:#9a8c74;--line:#3a2e22}
*{box-sizing:border-box}
body{font-family:'Segoe UI',Roboto,system-ui,sans-serif;color:var(--bone);margin:0;min-height:100vh;line-height:1.55;
 background:radial-gradient(1200px 520px at 50% -12%,#241a12 0%,transparent 60%),radial-gradient(900px 600px at 100% 120%,#1a1109 0%,transparent 55%),var(--bg)}
a{color:var(--gold);text-decoration:none}a:hover{color:#f0cf7a;text-decoration:underline}
.topbar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.6rem;
 padding:1rem 1.6rem;background:linear-gradient(180deg,#140d08,#0b0705);border-bottom:3px solid var(--red);position:relative}
.topbar:after{content:"";position:absolute;left:0;right:0;bottom:-3px;height:3px;
 background:repeating-linear-gradient(45deg,var(--gold) 0 14px,#0b0705 14px 28px);opacity:.45}
.brand{font-weight:800;letter-spacing:3px;font-size:1.25rem;text-transform:uppercase;color:var(--bone)}
.brand .seal{color:var(--gold);margin-right:.45rem;text-shadow:0 0 10px rgba(217,178,74,.6)}
.brand .sub{color:var(--red);font-size:.75rem;letter-spacing:2px;margin-left:.5rem}
nav a{color:var(--mute);text-transform:uppercase;letter-spacing:1.5px;font-size:.76rem;font-weight:700;margin-left:1.1rem}
nav a:hover{color:var(--gold)}
.wrap{max-width:860px;margin:2.2rem auto;padding:0 1.2rem}
.panel{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--line);border-left:4px solid var(--red);
 border-radius:6px;padding:1.7rem 1.9rem;box-shadow:0 18px 44px rgba(0,0,0,.55)}
h2{text-transform:uppercase;letter-spacing:2px;color:var(--red);font-size:1.3rem;margin:.1rem 0 1rem;border-bottom:1px solid var(--line);padding-bottom:.55rem}
h2:after{content:"";display:block;width:58px;height:3px;background:var(--gold);margin-top:.55rem}
label{display:block;font-size:.76rem;letter-spacing:1.3px;text-transform:uppercase;color:var(--mute);margin:.7rem 0 .15rem}
input{display:block;width:100%;max-width:360px;padding:.6rem .7rem;margin:.1rem 0 .3rem;background:#120d09;border:1px solid var(--line);border-radius:4px;color:var(--bone);font-size:1rem}
input:focus{outline:none;border-color:var(--red);box-shadow:0 0 0 3px rgba(177,18,38,.25)}
button{padding:.6rem 1.35rem;margin:.7rem 0;background:linear-gradient(180deg,var(--red),var(--red-d));color:var(--bone);border:none;border-radius:4px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;cursor:pointer;font-size:.84rem}
button:hover{filter:brightness(1.15)}
table{border-collapse:collapse;margin-top:1rem;width:100%}
th,td{border:1px solid var(--line);padding:.5rem .8rem;text-align:left}
th{background:var(--red-d);color:var(--bone);text-transform:uppercase;letter-spacing:1px;font-size:.76rem}
tr:nth-child(even) td{background:rgba(255,255,255,.02)}
td{font-family:Consolas,'Courier New',monospace;font-size:.9rem;color:#d8cdb5}
.err{color:#ff9a9a;background:rgba(177,18,38,.12);border-left:3px solid var(--red);padding:.6rem .9rem;border-radius:4px;margin-top:.8rem}
.err:before{content:"\\26A0  "}
.flag{color:var(--gold);font-weight:bold;font-size:1.1rem;font-family:Consolas,'Courier New',monospace;background:rgba(217,178,74,.08);border:1px dashed var(--gold);border-radius:4px;padding:.55rem .9rem;display:inline-block;margin-top:.6rem;text-shadow:0 0 10px rgba(217,178,74,.4);word-break:break-all}
.foot{text-align:center;color:var(--mute);font-size:.72rem;letter-spacing:2px;text-transform:uppercase;padding:1.4rem;margin-top:2rem;border-top:1px solid var(--line)}
p{margin:.6rem 0}
</style></head><body>
<header class="topbar">
<div class="brand"><span class="seal">&#9733;</span>Cartel de Sinaloa<span class="sub">// Red Interna</span></div>
<nav>{% if session.get('user') %}<a href="/recherche">Recherche</a><a href="/compte">Mon compte</a><a href="/logout">Deconnexion</a>{% else %}<a href="/login">Connexion</a>{% endif %}</nav>
</header>
<main class="wrap"><div class="panel">
{{ content|safe }}
</div></main>
<footer class="foot">Acceso restringido &middot; Solo personal autorizado &middot; {{ title }}</footer>
</body></html>"""

LOGIN_TPL = """<!-- FIXME securite : les identifiants sont colles dans la requete SQL sans etre filtres. A parametrer un jour. -->
<h2>Connexion</h2>
<p>Acces reserve aux membres du cartel. Identifiez-vous.</p>
<form method="post">
<label>Identifiant</label>
<input name="username" placeholder="identifiant">
<label>Mot de passe</label>
<input name="password" type="password" placeholder="mot de passe">
<button>Se connecter</button>
</form>
{% if error %}<p class="err">{{ error }}</p>{% endif %}"""

SEARCH_TPL = """<!-- note : les mots de passe sont stockes sous forme d'empreinte MD5 (32 caracteres hex). -->
<h2>Recherche de missions</h2>
<p>Base interne des operations du cartel.</p>
<form><input name="q" value="{{ q }}" placeholder="nom de mission..."><button>Chercher</button></form>
{% if err %}<p class="err">{{ err }}</p>{% endif %}
{% if rows %}<table>{% for r in rows %}<tr>{% for c in r %}<td>{{ c }}</td>{% endfor %}</tr>{% endfor %}</table>{% endif %}"""

COMPTE_TPL = """<!-- rappel : certaines pages existent hors du menu (penser a l'onglet Reseau du navigateur). -->
<!-- certaines reponses de l'API sont encodees en base64. -->
<h2>Bienvenue, {{ user }}</h2>
<p>Role : <strong>{{ role }}</strong></p>
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
<form method="post"><label>Code d'acces</label><input name="code" placeholder="code..."><button>Valider</button></form>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
{% endif %}"""


def page(title, tpl, **ctx):
    content = render_template_string(tpl, **ctx)
    return render_template_string(BASE, title=title, content=content)


MISSION1_TPL = """<!-- memo interne : le PIN fait 4 chiffres, de 0000 a 9999. Un programme teste tout ca tres vite. -->
<h2>Mission 1 : le coffre</h2>
<p>Le cartel a laisse un coffre chiffre. Telechargez-le, trouvez son PIN a 4 chiffres
avec un script, puis ouvrez-le. Le fichier contient l'adresse de l'intranet et le flag.</p>
<p><a href="/static/coffre.zip">&#9656; Telecharger coffre.zip</a></p>
<form method="post" action="/mission/1">
<label>Flag de l'etape 1</label>
<input name="flag" placeholder="FLAG{...}"><button>Valider le flag</button>
</form>
{% if msg %}<p class="{{ cls }}">{{ msg }}</p>{% endif %}
<p><a href="/login">Aller a l'intranet (etape 2) &rarr;</a></p>"""


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


OPERATION_EXTRAS = {
    3: {
        "operation": "Faire plaisir à ma dulciné",
        "deroule": ("Date : fin 2027, 14h00. Achat des ingrédients figurant dans la liste "
                    "de la page précédente, par les membres du cartel. Aucun vol d'ingrédient."),
    },
}

DOSSIER_TPL = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Dossier {{ d.id }} - {{ d.titre }}</title>
<style>
:root{--cork-a:#bf8b5c;--cork-b:#a46a42;--paper:#f7f0e1;--ink:#2a1d14;--red:#6b1a22;--red-bright:#b8102a}
body{margin:0;min-height:100vh;padding:24px 16px;font-family:Georgia,"Times New Roman",serif;
  background:radial-gradient(circle at 20% 10%,var(--cork-a),var(--cork-b));color:var(--ink)}
.feuille{position:relative;max-width:720px;margin:0 auto;background:var(--paper);
  padding:32px 28px;box-shadow:0 12px 30px rgba(0,0,0,.35);transform:rotate(-.4deg)}
.feuille::before{content:"";position:absolute;left:50%;top:-10px;width:18px;height:18px;margin-left:-9px;
  border-radius:50%;background:var(--red-bright);box-shadow:0 2px 4px rgba(0,0,0,.4)}
.tampon{display:inline-block;border:3px solid var(--red-bright);color:var(--red-bright);
  padding:4px 12px;font:700 14px "Courier New",monospace;letter-spacing:3px;transform:rotate(-6deg);opacity:.85}
h1{font-size:1.9rem;color:var(--red);margin:14px 0 6px;text-transform:uppercase;letter-spacing:1px}
.meta{font:14px "Courier New",monospace;color:#5b4a3a;margin-bottom:18px}
h2{font-size:1.1rem;color:var(--red);border-bottom:2px solid var(--red);padding-bottom:4px;margin-top:26px}
p{line-height:1.6;margin:8px 0}
.bloc{background:#fffaf0;border-left:4px solid var(--red);padding:12px 16px;margin-top:10px}
a{color:var(--red)}
</style></head><body>
<div class="feuille">
  <span class="tampon">CONFIDENTIEL</span>
  <h1>{{ d.titre }}</h1>
  <div class="meta">Dossier n° {{ d.id }} · Propriétaire : membre {{ d.owner_id }}</div>
  {% if operation %}<h2>Opération</h2><div class="bloc"><p><strong>{{ operation }}</strong></p></div>{% endif %}
  <h2>Contenu</h2>
  <div class="bloc"><p>{{ d.contenu }}</p></div>
  {% if deroule %}<h2>Déroulé</h2><div class="bloc"><p>{{ deroule }}</p></div>{% endif %}
  <p style="margin-top:28px"><a href="/recherche">Retour à l'intranet</a></p>
</div>
</body></html>"""


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
    payload.update(OPERATION_EXTRAS.get(dossier_id, {}))
    resp = make_response(jsonify(**payload))
    if dossier_id == 3:
        resp.headers["X-Mission-Trace"] = base64.b64encode(FLAG_API.encode()).decode()
    return resp


@app.route("/dossiers/<int:dossier_id>")
def dossier_page(dossier_id):
    if "user" not in session:
        return redirect(url_for("login"))
    # Requete parametree : cette page n'introduit pas de faille, la faille IDOR reste sur l'API.
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("SELECT id, owner_id, titre, contenu FROM dossiers WHERE id = ?",
                           (dossier_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        abort(404)
    d = dict(id=row[0], owner_id=row[1], titre=row[2], contenu=row[3])
    extras = OPERATION_EXTRAS.get(dossier_id, {})
    return render_template_string(DOSSIER_TPL, d=d, **extras)


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
