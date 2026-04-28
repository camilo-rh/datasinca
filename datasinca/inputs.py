import unicodedata
import datetime


MUESTREOS_VALIDOS = {'horario', 'diario', 'discreto'}
AGREGACIONES_VALIDAS = {'horario', 'diario', 'mensual', 'trimestral', 'anual'}

def input_muestreo(muestreo):
    if muestreo is None:
        muestreo = 'horario' # valor por defecto
    elif muestreo not in MUESTREOS_VALIDOS:
        raise ValueError(f"Muestreo no válido: {muestreo}")
    return muestreo

def input_agregacion(agregacion):
    if agregacion is not None and agregacion not in AGREGACIONES_VALIDAS:
        raise ValueError(f"Agregación no válida: {agregacion}")
    return agregacion

def input_altura(altura):
    if isinstance(altura, list) and all(isinstance(a, int) for a in altura):
        if any(a < 0 for a in altura):
            raise ValueError("Las alturas no pueden ser negativas")
        return altura
    elif isinstance(altura, int):
        if altura < 0:
            raise ValueError("La altura no puede ser negativa")
        return [altura]
    elif isinstance(altura, str) and altura.lower() == 's/i':
        return ['S/I']
    elif altura is None:
        return None
    raise ValueError(f"Altura no válida: {altura} - debe ser un entero, 'S/I', una lista de ellos, o None")

def input_region(regiones, df_regiones):
    if regiones is None:
        return df_regiones.index.tolist()

    if isinstance(regiones, (str, int)):
        regiones = [regiones]

    reg_map = build_region_map(df_regiones)

    ids = []

    for r in regiones:
        if isinstance(r, (str, int)):
            key = normalizar_string(str(r)).replace('regionde','').replace('region','')

            if key not in reg_map:
                raise ValueError(f"Región desconocida: {r}")

            ids.append(reg_map[key])
        else:
            raise TypeError("Solo strings y enteros soportados, o una lista con ellos")

    return ids

def input_est(estaciones, df_estaciones, mapto='id_est'):
    id_estaciones = []
    id_reg_est = set()

    if estaciones is None:
        return df_estaciones.index.tolist()
        
    if isinstance(estaciones, (str, int)):
        estaciones = [estaciones]

    est_map = build_est_map(df_estaciones, mapto)

    for est in estaciones:
        if isinstance(est, str):
            key = normalizar_string(est)

            if key not in est_map: # si no se encuentra, comprobar que no es un nombre duplicado (con sufijo de comuna)
                posibles = df_estaciones.loc[df_estaciones['nombre_est'].apply(normalizar_string) == key, :]

                if len(posibles) > 1: # si está duplicado, pedir agregar comuna al nombre
                    opciones = [f"{row['nombre_est']} ({row['comuna']})"
                                for _, row in posibles.iterrows()]
                    raise ValueError(f"Estación con nombre repetido: {est}. Usa una de estas:\n" +
                                     "\n".join(opciones))

                raise ValueError(f"Estación desconocida: {est}")
            
            id_est = est_map[key]
        elif isinstance(est, int):
            if est not in df_estaciones.index:
                raise ValueError(f"id_est inválido: {est}")
            id_est = est_map[est]

        if mapto == 'id_est':
            id_reg = [df_estaciones.loc[id_est,'id_reg']]
        else:
            id_reg = df_estaciones.loc[df_estaciones[mapto]==id_est, 'id_reg']
        id_reg_est.update(id_reg)
        id_estaciones.append(id_est)
    return id_estaciones, list(id_reg_est)

def input_param(parametros, df_parametros, mapto='cod_param'):
    param_map = build_param_map(df_parametros, mapto)

    if parametros is None:
        return df_parametros.index.tolist()

    if isinstance(parametros, str):
        parametros = [parametros]

    codigos = []

    for p in parametros:
        if isinstance(p, str):
            key = normalizar_string(p)
            if key not in param_map:
                raise ValueError(f"Parámetro desconocido: {p}")
            codigos.append(param_map[key])

        else:
            raise TypeError("Solo strings soportados por ahora")

    return codigos

def input_fecha(fecha):
    today = datetime.date.today()

    if fecha is None:
            fecha = datetime.date.today()

    # --- datetime/date ---
    if isinstance(fecha, datetime.datetime):
        fecha = fecha.date()
    elif isinstance(fecha, datetime.date):
        pass

    # --- int (días relativos) ---
    elif isinstance(fecha, int):
        if fecha <= 0:
            fecha = today + datetime.timedelta(days=fecha)
        elif fecha > 0:
            raise Exception('No puedes ingresar un entero positivo (fecha futura)')

    # --- string ---
    elif isinstance(fecha, str):
        fecha = fecha.strip()
        sep = None
        if '/' in fecha:
            sep = '/'
        elif '-' in fecha:
            sep = '-'
        if sep:
            parts = fecha.split(sep)
            if len(parts) != 3:
                raise ValueError("Formato de fecha inválido")

            d, m, y = parts
            if len(y) == 2:
                fmt = f'%d{sep}%m{sep}%y'
            elif len(y) == 4:
                fmt = f'%d{sep}%m{sep}%Y'
            else:
                raise ValueError("Formato de año inválido")

        elif fecha.isdigit():
            if len(fecha) == 6:
                fmt = '%d%m%y'
            elif len(fecha) == 8:
                fmt = '%d%m%Y'
            else:
                raise ValueError("Formato de fecha inválido. Debe ser dd/mm/yy, dd/mm/yyyy, ddmmyy o ddmmyyyy")
        else:
            raise ValueError("Formato de fecha inválido. Debe ser dd/mm/yy, dd/mm/yyyy, ddmmyy o ddmmyyyy")
        fecha = datetime.datetime.strptime(fecha, fmt).date()
    else:
        raise TypeError("Tipo de fecha no soportado")

    if fecha > today:
        raise ValueError('No se permiten fechas futuras')

    return fecha



def normalizar_string(s):
    try:
        s = unicodedata.normalize('NFD', s)
    except TypeError:
        print(s)
        raise
        # s = str(s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn') # Normalizar tildes
    return (s.lower().replace(" ", "").replace("_", "")
            .replace("-", "").replace(",", ".").replace(".", "")
            .replace("{", "").replace("}", "")).replace("'", "")

def build_param_map(df_parametros, mapto):
    param_map = {}

    for cod_param, row in df_parametros.iterrows():
        nombre = row['nombre_param']
        alias = row['alias_param']
        if mapto=='cod_param':
            dest=cod_param
        else:
            dest = row[mapto]

        param_map[normalizar_string(alias)] = dest
        param_map[normalizar_string(cod_param)] = dest
        param_map[normalizar_string(nombre)] = dest

    # alias útiles

    param_map.update(dict.fromkeys(['mp10'],param_map['pm10']))
    param_map.update(dict.fromkeys(['mp10d','pm10d','mp10discreto','pm10discreto'],param_map['pm1d']))
    param_map.update(dict.fromkeys(['mp25'],param_map['pm25']))
    param_map.update(dict.fromkeys(['mp25d','pm25d','mp25discreto','pm25discreto'],param_map['pm2d']))
    param_map.update(dict.fromkeys(['presion','presatm','presionatm'],param_map['pres']))
    param_map.update(dict.fromkeys(['precipitacion','lluvia'],param_map['rain']))
    param_map.update(dict.fromkeys(['rh','hr','humedadrelativa','hum','hume'], param_map['rhum']))
    param_map.update(dict.fromkeys(['temp','t','temperatura'],param_map['temp']))
    param_map.update(dict.fromkeys(['hct','thc','hidrocarburototal'],param_map['thcm']))
    param_map.update(dict.fromkeys(['wdir','dirviento','dv'], param_map['wdir']))
    param_map.update(dict.fromkeys(['wspd','velviento'], param_map['wspd']))
    
    return param_map

def build_est_map(df_estaciones, mapto):
    est_map = {}

    duplicados = set(
        df_estaciones['nombre_est'][ df_estaciones['nombre_est'].duplicated(keep=False) ]
        )
    for id_est, row in df_estaciones.iterrows():
        cod = row['cod_est']
        nombre = row['nombre_est']
        comuna = row['comuna']
        if mapto == 'id_est':
            dest = id_est
        else:
            dest = row[mapto]

        if not isinstance(cod, str):
            # print(f'nombre: {nombre} - cod: {cod} - id: {id_est} - comuna: {comuna}')
            continue
        est_map[normalizar_string(cod)] = dest
        est_map[id_est] = dest

        if nombre not in duplicados:
            est_map[normalizar_string(nombre)] = dest
        else:
            nombre_ext = f"{nombre} ({comuna})"
            est_map[normalizar_string(nombre_ext)] = dest
    return est_map

def build_region_map(df_regiones):
    reg_map = {}

    for id_reg, row in df_regiones.iterrows():
        cod_reg = row['cod_reg']
        nombre = row['nombre_region']

        reg_map[normalizar_string(cod_reg)] = id_reg
        reg_map[normalizar_string(id_reg)] = id_reg
        reg_map[normalizar_string(nombre)] = id_reg

    reg_map.update({
        'rm': 'M',
        '1': 'I',
        '2': 'II',
        '3': 'III',
        '4': 'IV',
        '5': 'V',
        '6': 'VI',
        '7': 'VII',
        '8': 'VIII',
        '9': 'IX',
        '10': 'X',
        '11': 'XI',
        '12': 'XII',
        '13': 'M',
        '14': 'XIV',
        '15': 'XV'
        })

    return reg_map