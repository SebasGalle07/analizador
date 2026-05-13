class ListaDinamica:
    def __init__(self, capacidad_inicial=8):
        if capacidad_inicial < 1:
            capacidad_inicial = 1
        self._datos = [None] * capacidad_inicial
        self._n = 0

    def __len__(self):
        return self._n

    def __iter__(self):
        i = 0
        while i < self._n:
            yield self._datos[i]
            i += 1

    def __getitem__(self, indice):
        return self.obtener(indice)

    def __setitem__(self, indice, valor):
        self.asignar(indice, valor)

    def _normalizar_indice(self, indice):
        if indice < 0:
            indice = self._n + indice
        if indice < 0 or indice >= self._n:
            raise IndexError("indice fuera de rango")
        return indice

    def _redimensionar(self, nueva_capacidad):
        nuevos = [None] * nueva_capacidad
        i = 0
        while i < self._n:
            nuevos[i] = self._datos[i]
            i += 1
        self._datos = nuevos

    def agregar(self, valor):
        if self._n == len(self._datos):
            self._redimensionar(len(self._datos) * 2)
        self._datos[self._n] = valor
        self._n += 1

    def extender(self, valores):
        for valor in valores:
            self.agregar(valor)

    def obtener(self, indice):
        indice = self._normalizar_indice(indice)
        return self._datos[indice]

    def asignar(self, indice, valor):
        indice = self._normalizar_indice(indice)
        self._datos[indice] = valor

    def intercambiar(self, indice_a, indice_b):
        indice_a = self._normalizar_indice(indice_a)
        indice_b = self._normalizar_indice(indice_b)
        temporal = self._datos[indice_a]
        self._datos[indice_a] = self._datos[indice_b]
        self._datos[indice_b] = temporal

    def insertar(self, indice, valor):
        if indice < 0:
            indice = 0
        if indice > self._n:
            indice = self._n
        if self._n == len(self._datos):
            self._redimensionar(len(self._datos) * 2)
        i = self._n
        while i > indice:
            self._datos[i] = self._datos[i - 1]
            i -= 1
        self._datos[indice] = valor
        self._n += 1

    def extraer(self, indice=None):
        if indice is None:
            indice = self._n - 1
        indice = self._normalizar_indice(indice)
        valor = self._datos[indice]
        i = indice
        while i < self._n - 1:
            self._datos[i] = self._datos[i + 1]
            i += 1
        self._datos[self._n - 1] = None
        self._n -= 1
        return valor

    def copiar(self):
        copia = ListaDinamica(self._n if self._n > 0 else 1)
        i = 0
        while i < self._n:
            copia.agregar(self._datos[i])
            i += 1
        return copia

    def sublista(self, inicio=0, fin=None):
        if fin is None or fin > self._n:
            fin = self._n
        if inicio < 0:
            inicio = self._n + inicio
        if inicio < 0:
            inicio = 0
        if fin < inicio:
            fin = inicio
        resultado = ListaDinamica(fin - inicio if fin - inicio > 0 else 1)
        i = inicio
        while i < fin:
            resultado.agregar(self._datos[i])
            i += 1
        return resultado

    def invertir_en_sitio(self):
        izquierda = 0
        derecha = self._n - 1
        while izquierda < derecha:
            self.intercambiar(izquierda, derecha)
            izquierda += 1
            derecha -= 1

    def esta_vacia(self):
        return self._n == 0

    def tamano(self):
        return self._n

    def a_lista(self):
        resultado = [None] * self._n
        i = 0
        while i < self._n:
            resultado[i] = self._datos[i]
            i += 1
        return resultado


class Pila:
    def __init__(self):
        self._datos = ListaDinamica()

    def apilar(self, valor):
        self._datos.agregar(valor)

    def desapilar(self):
        return self._datos.extraer()

    def esta_vacia(self):
        return self._datos.esta_vacia()

    def tamano(self):
        return self._datos.tamano()


class TablaHashSimple:
    def __init__(self, capacidad_inicial=16):
        capacidad = 1
        while capacidad < capacidad_inicial:
            capacidad *= 2
        self._claves = [None] * capacidad
        self._valores = [None] * capacidad
        self._ocupado = [False] * capacidad
        self._n = 0

    def __len__(self):
        return self._n

    def __iter__(self):
        i = 0
        while i < len(self._claves):
            if self._ocupado[i]:
                yield self._claves[i]
            i += 1

    def __getitem__(self, clave):
        valor = self.obtener(clave, None)
        if valor is None and not self.contiene(clave):
            raise KeyError(clave)
        return valor

    def __setitem__(self, clave, valor):
        self.poner(clave, valor)

    def _hash(self, clave):
        texto = str(clave)
        h = 0
        i = 0
        while i < len(texto):
            h = (h * 31 + ord(texto[i])) % len(self._claves)
            i += 1
        return h

    def _buscar_posicion(self, clave):
        indice = self._hash(clave)
        pasos = 0
        while pasos < len(self._claves):
            if not self._ocupado[indice] or self._claves[indice] == clave:
                return indice
            indice = (indice + 1) % len(self._claves)
            pasos += 1
        return -1

    def _redimensionar(self):
        claves_anteriores = self._claves
        valores_anteriores = self._valores
        ocupado_anterior = self._ocupado
        nueva_capacidad = len(self._claves) * 2
        self._claves = [None] * nueva_capacidad
        self._valores = [None] * nueva_capacidad
        self._ocupado = [False] * nueva_capacidad
        self._n = 0
        i = 0
        while i < len(claves_anteriores):
            if ocupado_anterior[i]:
                self.poner(claves_anteriores[i], valores_anteriores[i])
            i += 1

    def poner(self, clave, valor):
        if (self._n + 1) * 10 >= len(self._claves) * 7:
            self._redimensionar()
        indice = self._buscar_posicion(clave)
        if not self._ocupado[indice]:
            self._claves[indice] = clave
            self._ocupado[indice] = True
            self._n += 1
        self._valores[indice] = valor

    def obtener(self, clave, defecto=None):
        indice = self._hash(clave)
        pasos = 0
        while pasos < len(self._claves):
            if not self._ocupado[indice]:
                return defecto
            if self._claves[indice] == clave:
                return self._valores[indice]
            indice = (indice + 1) % len(self._claves)
            pasos += 1
        return defecto

    def contiene(self, clave):
        marcador = object()
        return self.obtener(clave, marcador) is not marcador

    def claves(self):
        resultado = ListaDinamica(self._n if self._n > 0 else 1)
        i = 0
        while i < len(self._claves):
            if self._ocupado[i]:
                resultado.agregar(self._claves[i])
            i += 1
        return resultado.a_lista()

    def valores(self):
        resultado = ListaDinamica(self._n if self._n > 0 else 1)
        i = 0
        while i < len(self._valores):
            if self._ocupado[i]:
                resultado.agregar(self._valores[i])
            i += 1
        return resultado.a_lista()

    def pares(self):
        resultado = ListaDinamica(self._n if self._n > 0 else 1)
        i = 0
        while i < len(self._claves):
            if self._ocupado[i]:
                resultado.agregar((self._claves[i], self._valores[i]))
            i += 1
        return resultado.a_lista()

    def a_diccionario(self):
        resultado = {}
        i = 0
        while i < len(self._claves):
            if self._ocupado[i]:
                resultado[self._claves[i]] = self._valores[i]
            i += 1
        return resultado

    def esta_vacia(self):
        return self._n == 0

    def tamano(self):
        return self._n


class ConjuntoManual:
    def __init__(self):
        self._datos = ListaDinamica()

    def agregar(self, valor):
        if not self.contiene(valor):
            self._datos.agregar(valor)

    def contiene(self, valor):
        i = 0
        while i < self._datos.tamano():
            if self._datos[i] == valor:
                return True
            i += 1
        return False

    def a_lista(self):
        return self._datos.a_lista()

    def tamano(self):
        return self._datos.tamano()


def lista_desde_iterable(iterable):
    resultado = ListaDinamica()
    for valor in iterable:
        resultado.agregar(valor)
    return resultado.a_lista()


def copiar_lista(lista):
    resultado = ListaDinamica(len(lista) if len(lista) > 0 else 1)
    i = 0
    while i < len(lista):
        resultado.agregar(lista[i])
        i += 1
    return resultado.a_lista()


def sublista(lista, inicio=0, fin=None):
    n = len(lista)
    if fin is None or fin > n:
        fin = n
    if inicio < 0:
        inicio = n + inicio
    if inicio < 0:
        inicio = 0
    if fin < inicio:
        fin = inicio
    resultado = ListaDinamica(fin - inicio if fin - inicio > 0 else 1)
    i = inicio
    while i < fin:
        resultado.agregar(lista[i])
        i += 1
    return resultado.a_lista()


def ultimos_elementos(lista, cantidad):
    n = len(lista)
    inicio = n - cantidad
    if inicio < 0:
        inicio = 0
    return sublista(lista, inicio, n)


def invertir_lista(lista):
    izquierda = 0
    derecha = len(lista) - 1
    while izquierda < derecha:
        temporal = lista[izquierda]
        lista[izquierda] = lista[derecha]
        lista[derecha] = temporal
        izquierda += 1
        derecha -= 1


def extraer_en_indice(lista, indice):
    n = len(lista)
    if indice < 0:
        indice = n + indice
    if indice < 0 or indice >= n:
        raise IndexError("indice fuera de rango")
    valor = lista[indice]
    i = indice
    while i < n - 1:
        lista[i] = lista[i + 1]
        i += 1
    return sublista(lista, 0, n - 1), valor


def insertar_en_indice(lista, indice, valor):
    n = len(lista)
    if indice < 0:
        indice = 0
    if indice > n:
        indice = n
    resultado = [None] * (n + 1)
    i = 0
    while i < indice:
        resultado[i] = lista[i]
        i += 1
    resultado[indice] = valor
    while i < n:
        resultado[i + 1] = lista[i]
        i += 1
    return resultado


def concatenar_iterables(a, b):
    resultado = ListaDinamica()
    for valor in a:
        resultado.agregar(valor)
    for valor in b:
        resultado.agregar(valor)
    return resultado.a_lista()


def crear_lista_rellena(valor, cantidad):
    resultado = [None] * cantidad
    i = 0
    while i < cantidad:
        resultado[i] = valor
        i += 1
    return resultado


def crear_lista_de_listas(cantidad):
    resultado = [None] * cantidad
    i = 0
    while i < cantidad:
        resultado[i] = ListaDinamica()
        i += 1
    return resultado


def crear_matriz(filas, columnas, valor):
    matriz = [None] * filas
    i = 0
    while i < filas:
        matriz[i] = crear_lista_rellena(valor, columnas)
        i += 1
    return matriz


def menor_de_dos(a, b):
    if a < b:
        return a
    return b


def mayor_de_dos(a, b):
    if a > b:
        return a
    return b


def menor_de_tres(a, b, c):
    menor = a
    if b < menor:
        menor = b
    if c < menor:
        menor = c
    return menor


def mayor_de_tres(a, b, c):
    mayor = a
    if b > mayor:
        mayor = b
    if c > mayor:
        mayor = c
    return mayor


def menor_de_varios(valores):
    if len(valores) == 0:
        return None
    menor = valores[0]
    i = 1
    while i < len(valores):
        if valores[i] < menor:
            menor = valores[i]
        i += 1
    return menor


def mayor_de_varios(valores):
    if len(valores) == 0:
        return None
    mayor = valores[0]
    i = 1
    while i < len(valores):
        if valores[i] > mayor:
            mayor = valores[i]
        i += 1
    return mayor


def sumatoria(valores):
    total = 0
    for valor in valores:
        total += valor
    return total


def obtener_valor(diccionario, clave, defecto=None):
    if diccionario is None:
        return defecto
    if clave in diccionario:
        return diccionario[clave]
    return defecto


def claves_diccionario(diccionario):
    resultado = ListaDinamica()
    for clave in diccionario:
        resultado.agregar(clave)
    return resultado.a_lista()


def valores_diccionario(diccionario):
    resultado = ListaDinamica()
    for clave in diccionario:
        resultado.agregar(diccionario[clave])
    return resultado.a_lista()


def pares_diccionario(diccionario):
    resultado = ListaDinamica()
    for clave in diccionario:
        resultado.agregar((clave, diccionario[clave]))
    return resultado.a_lista()


def asegurar_lista_en_diccionario(diccionario, clave):
    if clave not in diccionario:
        diccionario[clave] = []
    return diccionario[clave]


def eliminar_primera_clave(diccionario):
    for clave in diccionario:
        del diccionario[clave]
        return True
    return False


def vaciar_diccionario(diccionario):
    claves = claves_diccionario(diccionario)
    i = 0
    while i < len(claves):
        del diccionario[claves[i]]
        i += 1


def ordenar_por_seleccion(valores, es_menor):
    resultado = copiar_lista(valores)
    n = len(resultado)
    i = 0
    while i < n - 1:
        menor_idx = i
        j = i + 1
        while j < n:
            if es_menor(resultado[j], resultado[menor_idx]):
                menor_idx = j
            j += 1
        if menor_idx != i:
            temporal = resultado[i]
            resultado[i] = resultado[menor_idx]
            resultado[menor_idx] = temporal
        i += 1
    return resultado
