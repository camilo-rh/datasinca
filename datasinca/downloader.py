import requests
import re
from lxml import html
import pandas as pd
from io import StringIO

BASE_URL = "https://sinca.mma.gob.cl"
URL_ESTACION = BASE_URL + "/index.php/estacion/index/id/"
URL_DESCARGA = BASE_URL + "/cgi-bin/APUB-MMA/apub.tsindico2.cgi?outtype=txt&macro=./"
AGREGACION_DEFECTO = {'horario': 'horario',
                     'diario': 'diario',
                     'discreto': 'diario'}

def build_url(inicio,fin,codparam,altura,codest,codreg,muestreo,agregacion,tipo_param):
        codaltura = str(altura if altura != "S/I" else 0).rjust(3, '0')
        agregacion = AGREGACION_DEFECTO.get(muestreo, 'horario') if agregacion is None else agregacion
        url = f"{URL_DESCARGA}{codreg}/{codest}/"

        if tipo_param == 'cal':
            url += f'Cal/{codparam}//{codparam}.{muestreo}.{agregacion}'
        elif tipo_param == 'met':
            url += f'Met/{codparam}//{muestreo}_{codaltura}'
            if codparam == 'WDIR':
                url += '_spec'
        else:
            raise ValueError(f'Tipo de parámetro no reconocido: {tipo_param}')
        
        url += f'.ic&from={inicio}&to={fin}&path=/usr/airviro/data/CONAMA/&lang=esp&rsrc=&macropath='
        return url

class Transport:
    def __init__(self, timeout=10, session=None):
        self.timeout = timeout
        self._external_session = session is not None
        self.session = session or self._build_session()

    def _build_session(self):
        s = requests.Session()
        s.headers.update({"User-Agent": "datasinca/0.1"}) # User-Agent propio para identificar datasinca frente al servidor
        return s
    
    def get(self, url):
        try:
            return self._request(url)
        except (requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout):
            # https a http
            if url.startswith("https://"):
                fallback_url = url.replace("https://", "http://", 1)
                return self._request(fallback_url)
            raise
    def _request(self, url):
        r = requests.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r

    def close(self):
        if not self._external_session and self.session:
            self.session.close()

def descargar_serie(inicio, fin, cod_reg, cod_est, cod_param, altura, muestreo, agregacion, tipo_param, transport=None):
    url = build_url(inicio,fin,cod_param,altura,cod_est,cod_reg,muestreo,agregacion,tipo_param)
    transport = transport or Transport()
    return transport.get(url)


def descargar_mensaje_estacion(transport, id_est, include_tablas=False):
    text = transport.get(URL_ESTACION + str(id_est)).text

    tree = html.fromstring(text)
    div = tree.xpath('//div[contains(@class, "mensajeStn")]')
    if not div:
        return None
    
    div = div[0]

    div_text = html.tostring(div, encoding='unicode')
    match = re.search(r'<table\b.*?</table>', div_text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return limpiar_mensaje_elemento(div)
    
    if not include_tablas:
        tablas = div.xpath('.//table')
        for tabla in tablas:
            tabla.getparent().remove(tabla)
        return limpiar_mensaje_elemento(div)

    tabla = match.group()
    df = pd.read_html(StringIO(tabla))[0]
    tabla = df.to_string(index=False)
    tabla = "\n".join(f"\t{line}" for line in tabla.splitlines())

    prev = html.fromstring(div_text[:match.start()])
    post = html.fromstring(div_text[match.end():])
    prev = limpiar_mensaje_elemento(prev)
    post = limpiar_mensaje_elemento(post)

    mensaje = (prev + "\n" + tabla + "\n" + post).strip()

    return mensaje

def limpiar_mensaje_elemento(elem):
    texto = elem.text_content()
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

