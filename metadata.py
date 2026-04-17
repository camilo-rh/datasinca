from pathlib import Path
import pandas as pd
def load_metadata(data_path):
    if data_path is None:
        base_path = Path(__file__).parent / "data"
    else:
        base_path = Path(data_path)
        if not base_path.is_absolute():
            base_path = Path.cwd() / base_path
    regiones = pd.read_csv(base_path / "regiones.csv", sep=';')
    estaciones = pd.read_csv(base_path / "estaciones.csv", sep=';', dtype={'id_est': 'Int64', 'cod_est': 'string', 'id_reg': 'string'})
    parametros = pd.read_csv(base_path / "parametros.csv", sep=';', dtype={'cod_param': 'string', 'nombre_param': 'string'})
    series = pd.read_csv(base_path / "series.csv", sep=';', dtype={'id_serie': 'Int64', 'id_est': 'Int64', 'cod_param': 'string', 'altura': 'Int64'})
    
    regiones.set_index('id_reg', inplace=True)
    estaciones.set_index('id_est', inplace=True)
    parametros.set_index('cod_param', inplace=True)
    series.set_index(['id_est', 'cod_param'], inplace=True)
    
    return regiones, estaciones, parametros, series