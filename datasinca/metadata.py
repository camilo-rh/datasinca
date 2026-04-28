from pathlib import Path
import pandas as pd

class SincaMetadata:
    def __init__(self, regiones, estaciones, parametros, series):
        self.regiones = regiones
        self.estaciones = estaciones
        self.parametros = parametros
        self.series = series

    def __repr__(self):
        return (
            f"SincaMetadata("
            f"regiones={len(self.regiones)}, "
            f"estaciones={len(self.estaciones)}, "
            f"parametros={len(self.parametros)}, "
            f"series={len(self.series)})"
        )

def load_metadata(data_path=None):
    if data_path is None:
        base_path = Path(__file__).parent / "data"
    else:
        base_path = Path(data_path)
        if not base_path.is_absolute():
            base_path = Path.cwd() / base_path
    regiones = pd.read_csv(base_path / "regiones.csv", sep=';')
    estaciones = pd.read_csv(base_path / "estaciones.csv", sep=';', dtype={'id_est': 'Int64', 'cod_est': 'string', 'id_reg': 'string'})
    parametros = pd.read_csv(base_path / "parametros.csv", sep=';', dtype={'cod_param': 'string', 'nombre_param': 'string', 'alias_param': 'string'})
    series = pd.read_csv(base_path / "series.csv", sep=';', dtype={'id_est': 'Int64', 'cod_param': 'string', 'altura': 'Int64', 'id_reg': 'string'})
    
    series['altura'] = series['altura'].astype('object').fillna('S/I')

    regiones.set_index('id_reg', inplace=True)
    estaciones.set_index('id_est', inplace=True)
    parametros.set_index('cod_param', inplace=True)
    series = series.set_index(['id_est', 'cod_param']).sort_index()
    
    return SincaMetadata(regiones, estaciones, parametros, series)