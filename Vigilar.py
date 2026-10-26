import json, os, unicodedata, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 14)"}
PALABRAS = ["adviento", "calendario"]
TIENDA = "https://www.maquillajetrendyshop.com"
TOPIC = os.environ.get("TOPIC_TRENDY")

def plano(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def avisar(titulo, msg, link=None):
    if not TOPIC:
        print("falta el tema de ntfy")
        return
    h = {"Title": titulo, "Priority": "5", "Tags": "tada"}
    if link:
        h["Click"] = link
    try:
        req = urllib.request.Request("https://ntfy.sh/" + TOPIC,
            data=msg.encode("utf-8"), headers=h, method="POST")
        urllib.request.urlopen(req, timeout=20).read()
        print("aviso enviado")
    except Exception as e:
        print("no pude avisar:", e)

def buscar():
    res = {}
    for w in PALABRAS:
        url = TIENDA + "/api/catalog_system/pub/products/search?ft=" + w + "&_from=0&_to=49"
        for p in get_json(url):
            nombre = p.get("productName", "")
            if any(x in plano(nombre) for x in PALABRAS):
                stock = any(s.get("commertialOffer", {}).get("AvailableQuantity", 0) > 0
                            for i in p.get("items", []) for s in i.get("sellers", []))
                res[p.get("linkText", nombre)] = {
                    "nombre": nombre, "stock": stock,
                    "url": TIENDA + "/" + p.get("linkText", "") + "/p"}
    return res

try:
    estado = json.load(open("estado.json"))
except Exception:
    estado = {}

if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
    avisar("Vigilante Trendy en la nube activo", "Las notificaciones funcionan.")

try:
    ahora = buscar()
    print("coincidencias:", len(ahora))
    for k, d in ahora.items():
        antes = estado.get(k)
        if antes is None:
            avisar("Salio el calendario de Trendy",
                   d["nombre"] + (" - CON STOCK" if d["stock"] else " - aun sin stock"), d["url"])
        elif d["stock"] and not antes["stock"]:
            avisar("Ya hay stock en Trendy", d["nombre"], d["url"])
        estado[k] = d
except Exception as e:
    print("ERROR:", e)

                     json.dump(estado, open("estado.json", "w"), indent=1)
