class DataSINCA:
    def __init__(self, data, validez, unidades):
        self.data = data # dataframe con datos de la serie, indexado por datetime
        self.validez = validez # dataframe con validez de cada dato, indexado por datetime
        self.unidades = unidades # diccionario con una clave por cada columna de datos, con su unidad de medida correspondiente
        self.fuente = 'SINCA'

    def filtrar_validez(self, nivel):
        return self.data[self.validez == nivel]

    def solo_validos(self):
        return self.filtrar_validez('validado')