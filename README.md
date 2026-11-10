# Atelier cartel - intranet

Lancer : `docker compose up -d --build` puis ouvrir `http://<IP-DU-PC>:8000`.
Reinitialiser la base entre deux groupes : `http://<IP-DU-PC>:8000/reset?token=prof`.
Le token se change avec la variable d'environnement RESET_TOKEN.

Flags (a configurer dans CTFd) :
1. FLAG{pin_brute_force_ok} : dans le ZIP (PIN 0731)
2. FLAG{sqli_union_ok} : affiche par la SQLi UNION (compte sys_audit)
3. FLAG{hash_cracked_ok} : affiche sur /compte une fois connecte en chef
4. FLAG{hidden_routes_ok} : /chef/salle-secrete, code ALPHA-7731 (en-tete X-Code-Acces de /api/v1/statut)
5. FLAG{api_chain_ok} : /api/v1/dossiers/3 (en-tete X-Mission-Trace, base64)

Mot de passe du chef : cobraNoir1978 (ne pas divulguer).
