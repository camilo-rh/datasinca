class DataSINCA:
    def __init__(self, data, validez):
        self.data = data # dataframe con datos de la serie, indexado por datetime
        self.validez = validez # dataframe con validez de cada dato, indexado por datetime

    def filtrar_validez(self, nivel): # nan, 'sin_info', 'validado', 'preliminar', 'novalidado'
        mask = self.validez == nivel
        return DataSINCA(self.data[mask], self.validez[mask])

    def solo_validos(self):
        return self.filtrar_validez('validado')
    
    def estaciones(self):
        return self.data.columns.get_level_values('estacion').unique().tolist()
    
    def parametros(self):
        return self.data.columns.get_level_values('parametro').unique().tolist()
    
    def periodo(self):
        return (self.data.index.min(), self.data.index.max())
    
    def conteo_validez(self):
        return self.validez.apply(lambda x: x.value_counts(dropna=False)).sum(axis=1)
    
    def resumen(self):
        """
        Metodo de inspección rápida. Muestra número de estaciones, parámetros, periodo cubierto, y conteo de datos por nivel de validez.
        """
        num_estaciones = self.data.columns.get_level_values('estacion').nunique()
        num_parametros = self.data.columns.get_level_values('parametro').nunique()
        periodo = (self.data.index.min(), self.data.index.max())
        conteo_validez = self.validez.apply(lambda x: x.value_counts(dropna=False)).sum(axis=1)
        
        print(f"Numero de estaciones: {num_estaciones}")
        print(f"Numero de parámetros: {num_parametros}")
        print(f"Periodo: {periodo[0].date()} a {periodo[1].date()}")
        print("Conteo por validez:")
        print(conteo_validez)


    
    def __repr__(self):
        return f"DataSINCA(data.shape={self.data.shape})"