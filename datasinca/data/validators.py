def _xval_estacion(id_estaciones, seleccion, df_estaciones):
    idx_estaciones = seleccion.index.get_level_values(0).unique()
    ids_validos = idx_estaciones.intersection(id_estaciones)

    if len(ids_validos) != len(id_estaciones):
        faltantes = set(id_estaciones) - set(ids_validos)
        id_regiones_disp = seleccion.loc[(idx_estaciones, slice(None)), 'id_reg'].unique().tolist()
        nombre_est_disp = df_estaciones.loc[idx_estaciones, 'nombre_est'].sort_index()
        
        estaciones_str = "\n".join(f"  - {i}: {n}" for i, n in nombre_est_disp.items())
        raise ValueError(
            f"Estación(es) no válida(s): {sorted(faltantes)}.\n\n"
            f"No son compatibles con la configuración actual:\n"
            f"  - región: {id_regiones_disp}\n"
            f"Estaciones disponibles en la selección actual:\n{estaciones_str}"
        )

def _xval_parametro(cod_params, seleccion, df_estaciones, df_parametros):
    idx_parametros = seleccion.index.get_level_values(1).unique()
    cods_validos = idx_parametros.intersection(cod_params)

    if len(cods_validos) != len(cod_params):
        faltantes = set(cod_params) - set(cods_validos)
        id_estaciones_sel = seleccion.index.get_level_values(0).unique().tolist()
        nom_estaciones_sel = df_estaciones.loc[id_estaciones_sel, 'nombre_est'].tolist()
        nom_params = df_parametros.loc[sorted(faltantes), 'nombre_param'].tolist()
        nom_params_disp = df_parametros.loc[idx_parametros, 'nombre_param'].sort_index()
        parametros_str = "\n".join(f"  - {c}: {n}" for c, n in nom_params_disp.items())
        raise ValueError(
            f"Parámetro(s) no válido(s): {nom_params}.\n\n"
            f"No son compatibles con la configuración actual:\n"
            f"  - estación(es): {nom_estaciones_sel}\n"
            f"Parámetros disponibles en la selección actual:\n{parametros_str}"
        )    

def _xval_altura(alturas, seleccion, df_estaciones, df_parametros):
    idx_alturas = seleccion['altura'].unique()
    alturas_validas = set(idx_alturas).intersection(alturas)

    if len(alturas_validas) != len(alturas):
        faltantes = set(alturas) - set(alturas_validas)
        id_estaciones = seleccion.index.get_level_values(0).unique().tolist()
        nombre_est = df_estaciones.loc[id_estaciones, 'nombre_est'].tolist()
        cod_params = seleccion.index.get_level_values(1).unique().tolist()
        nombre_param = df_parametros.loc[cod_params, 'nombre_param'].tolist()
        id_reg = seleccion['id_reg'].unique().tolist()
        raise ValueError(
            f"Altura(s) no válida(s): {sorted(faltantes)}.\n\n"
            f"No son compatibles con la configuración actual:\n"
            f"  - región: {id_reg}\n"
            f"  - estación(es): {nombre_est}\n"
            f"  - parámetro(s): {nombre_param}\n\n"
            f"Alturas disponibles en este contexto:\n"
            f"  {sorted(idx_alturas.tolist())}"
        )
    
# def _xval_region(id_regiones, seleccion):
#     idx_regiones = seleccion['id_reg'].unique()
#     ids_validos = set(idx_regiones).intersection(id_regiones)

#     if len(ids_validos) != len(id_regiones):
#         faltantes = set(id_regiones) - set(ids_validos)
#         raise ValueError(
#             f"Región(es) no válida(s): {sorted(faltantes)}.\n\n"
#             f"Las estaciones seleccionadas pertenecen a la(s) región(es):\n"
#             f"{idx_regiones.tolist()}\n\n"
#             "Puedes crear una nueva instancia con la configuración deseada:\n"
#             f"  sinca = Sinca(region={id_regiones[0] if len(id_regiones) == 1 else id_regiones})\n\n"
#         )