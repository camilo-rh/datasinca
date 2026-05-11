# datasinca

datasinca es una librería en Python para **descargar y estructurar** datos históricos del **SINCA** (Sistema de Información Nacional de Calidad del Aire) del Ministerio del Medio Ambiente de Chile, entregándolos en formatos listos para exportación o análisis con `pandas`.

Provee:  
- un cliente de descarga `Sinca`, para obtener datos mediante filtros basados en metadata
- una clase `DataSinca`, basada en pandas, para estructurar y analizar las series


##  Instalación
```bash
pip install git+https://github.com/camilo-rh/datasinca.git
```
<br>

## Uso del cliente de descarga `Sinca`

```python
from datasinca import Sinca

sinca = Sinca()

# Exploración
sinca.region # ver regiones disponibles
sinca.region = 13 # seleccionar región ("Metropolitana" o "M")
sinca.estacion # ver estaciones seleccionadas por elección de región
sinca.parametro # ver parámetros seleccionados por elección de región

# Descarga
ds = sinca.descarga(
        inicio = "2024-03-01",
        fin = -1, # relativo a hoy: -1 = ayer
        parametro = ["pm25","pm10","wdir"],
        )

# acceso directo a pandas DataFrame
df = ds.data    # ds.data.copy()  Si modificarás el DataFrame, se recomienda trabajar sobre una copia

# exportar a CSV
df.to_csv("datos.csv")
```

### Argumentos de descarga

| Argumento |       Tipo      | Default |          Descripción                 |
|----------|------------------|--------|------------------------------|
| `inicio` | `str` `int` `datetime` | 0 (hoy)    | (opcional) Fecha inicial <br>`str`: string ISO ("YYYY-MM-DD") o formato SINCA ("yymmdd") <br> `int`: entero relativo a hoy (ej: `-1` = ayer) |
| `fin` | `str` `int` `datetime`    | 0 (hoy)    | (opcional) Fecha final de descarga.<br> Acepta mismos formatos que `inicio` |
| `region` | `int` `str` `list`   | (todas)   | (opcional) Regiones a consultar, disponibles en `sinca.region`. <br> Acepta nombres, IDs (números romanos), enteros o listas de ellos. <br> `str` case-insensitive |
| `estacion` | `int` `str` `list` | (todas) | (opcional) Estaciones a consultar, disponibles en `sinca.estacion`. <br> Acepta nombres, IDs, enteros o listas de ellos. <br> `str` case-insensitive |
| `parametro` | `str` `list` | (todos) | (opcional) Parámetros a descargar, disponibles en `sinca.parametro`. <br> Acepta nombres, códigos, aliases comunes (ej: `"pm25"`, `"PM2.5"`, `"MP2.5"`) o listas de ellos <br> `str` case-insensitive |
| `altura` | `int` `str` `list` | (todas) | (opcional) Altura de medición (solo meteorología) <br>  contaminantes: `"S/I"`; meteorología: `"S/I"`, enteros o listas de ellos <br> Por defecto, dado una estación y parámetro, consulta por todas las alturas disponibles (según metadata interna) |
| `registro` | `str` | "horario" | (opcional) Tipo de muestreo. <br> `"horario"` <br> `"diario"` <br> `"discreto"`: para "PM10 discreto" y "PM25 discreto" |


### Comportamiento del cliente de descarga `Sinca`

Los filtros de descarga también se pueden configurar en el constructor y como atributos
```python
sinca = Sinca(estacion = 'osorno')
sinca.inicio = '2026-03-01'
```
de esta manera la configuración se conserva y permite explorar dinámicamente las opciones disponibles
```python
>>> sinca.parametro
                          nombre_param alias_param
cod_param                                         
PM10        Material particulado MP 10        PM10
PM25       Material particulado MP 2,5        PM25
RHUM         Humedad relativa del aire          RH
TEMP              Temperatura ambiente        TEMP
WDIR              Dirección del viento        WDIR
WSPD              Velocidad del viento        WSPD

>>> sinca.parametro = ['pm10', 'pm25']
>>> ds = sinca.descarga()
```

#### Jerarquía de configuración
Cuatro de los filtros siguen una jerarquía:  
`region` $>$ `estacion` $>$ `parametro` $>$ `altura`  
  
- La configuración debe ser consistente con niveles superiores\
	(ej: `sinca.region=[9,10]` → `sinca.estacion='parqueohiggins'` → error)  

- Los niveles inferiores se expanden automáticamente\
	(ej: seleccionar una estación incluye todos sus parámetros disponibles)



### Log
Para trazabilidad (mensajes de estación, errores de comunicación con el servidor SINCA), se puede activar logging
```python
sinca = Sinca(log=True) #la instancia guardará un archivo log en /home/usuario/.datasinca/logs/
```


<br>

## ¿Qué obtienes tras la descarga?

La descarga entrega datos históricos del SINCA estructurados para exportación o análisis con `pandas`.\
`ds` es una instancia de `DataSinca`, un contenedor que organiza:

### `ds.data`
`pandas.DataFrame` con datos históricos del SINCA.

### `ds.validacion`
`pandas.DataFrame` con el estado de validación de cada dato\
Valores posibles:
- `'validado'`
- `'preliminar'`
- `'novalidado'`
- `NaN` → no aplica (variables meteorológicas) o dato faltante

Ambos dataframes poseen:
- índice temporal (`datetime`)
- columnas `MultiIndex`: (comuna, estacion, parametro, unidad, altura)


Los datos de SINCA incluyen dos tipos de `parametro`s:
- **Contaminantes** → tienen estado de validación: `validado`, `preliminar` o `novalidado`
- **Meteorológicos** → actualmente **no tienen información de validación** en SINCA

*Nota: Los parámetros meteorológicos mantienen una columna en `ds.validacion` con `NaN` para conservar una estructura consistente del dataset.*


## Uso de `DataSinca`

### Uso recomendado

```python
# eliminar columnas vacías
ds = ds.drop_empty_columns()

# separar contaminantes de meteorológicos
ds_cont, ds_meteo = ds.sep_contam_meteo()

# filtrar contaminantes por nivel de validación (meteorología no tiene validación en el SINCA)
dsc_filt = ds_cont.filtrar_validacion(["validado", "preliminar"])
```

Antes de exportar los datos o trabajar directamente con `pandas.DataFrame`, se recomienda aplanar (o reordenar) los niveles de las columnas, conservando solo la información de interés.
```python
# Aplanar niveles ('parametro', 'unidad' y 'altura') a un único nivel y borrar los demás
dsm_flat = ds_meteo.flatten_levels(['parametro','unidad','altura'])

# Aplanar solo los niveles que tienen más de un valor
dsc_flat = dsc_filt.flatten_nonconstant_levels()
```
Finalmente
```python
# obtener DataFrame de datos
df = dsm_flat.data.copy()

# exportar a CSV
dsc_flat.data.to_csv('parametros_contaminantes.csv')
```


<br>

### Otros métodos de `DataSinca`

#### Separación de tipos contaminantes/meteorológicos
```python
ds_contam = ds.contaminantes()    # solo contaminantes
ds_meteo = ds.meteorologicos()   # solo meteorológicos
ds_contam, ds_meteo = ds.sep_contam_meteo()
```

#### Validación
Los métodos de validación aplican **solo a contaminantes**:
```python
ds.conteo_validacion()
ds_filt = ds_contam.filtrar_validacion(["validado","preliminar"])
```

Comportamiento:
- Dataset **mixto** → _(warning)_ se consideran solo columnas con información de validación
- Dataset sin información de validación (p.ej. solo meteorológicos) → error
- Datos faltantes (`NaN`) → **no se consideran estados de validación**

#### Inspección rápida
```python
ds.resumen()
```

#### Reordenar niveles de las columnas (MultiIndex)
```python
# intercambiar nivel 'parametro' con nivel 0
ds_swap = ds.swap_levels('parametro', 0)
# ahora 'parametro' es el nivel expuesto
ds_swap.data['PM25']
```

#### Selección de datos
##### Selección estructurada
```python
ds_sel = ds.sel(estacion="parque ohiggins", parametro="pm25")
```

##### Múltiples valores
```python
ds_sel = ds.sel(parametro=["pm25", "pm10"])
```

##### Altura
Para contaminantes la altura siempre es `"S/I"` (sin información)
```python
ds_sel = ds.sel(altura=10)
ds_sel = ds.sel(altura="10m")
ds_sel = ds.sel(altura="S/I")
```

##### Búsqueda flexible de estaciones
```python
ds_sel = ds.buscar_estacion("acreditada")
```

```python
ds_sel = ds.buscar_estacion(["parque", "pudahuel"])
```

#### Filtrar por fecha
```python
ds.entre("010326", "100326") # 1 de marzo a 10 de marzo del 2026
```

<br>
<br>

## Licencia

MIT License


