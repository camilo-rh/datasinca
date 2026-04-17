class DataSINCA:
    def __init__(self, data, validez, unidades):
        self.data = data
        self.validez = validez
        self.unidades = unidades
        self.fuente = 'SINCA'

    def filtrar_validez(self, nivel):
        return self.data[self.validez == nivel]

    def solo_validos(self):
        return self.filtrar_validez('validado')