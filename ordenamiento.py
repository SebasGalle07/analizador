import csv
import time


def cargar_dataset(ruta_archivo):
    dataset = []
    try:
        with open(ruta_archivo, mode="r", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                dataset.append(fila)
        print(f"[OK] Dataset cargado. Total de filas: {len(dataset)}")
    except Exception as error:
        print(f"[ERROR] No se pudo leer el archivo: {error}")
    return dataset


def cronometrar(func):
    def envoltura(*args, **kwargs):
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        fin = time.perf_counter()
        tiempo_ms = (fin - inicio) * 1000
        return resultado, tiempo_ms

    return envoltura


def obtener_cierre(registro, simbolo="VOO"):
    try:
        return float(registro.get(f"{simbolo}_Close", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def obtener_volumen(registro, simbolo="VOO"):
    try:
        return float(registro.get(f"{simbolo}_Volume", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def fecha_a_entero(registro):
    return int(registro["Fecha"].replace("-", ""))


def es_estrictamente_menor(registro_a, registro_b, simbolo="VOO"):
    fecha_a = registro_a["Fecha"]
    fecha_b = registro_b["Fecha"]

    close_a = obtener_cierre(registro_a, simbolo=simbolo)
    close_b = obtener_cierre(registro_b, simbolo=simbolo)

    if fecha_a != fecha_b:
        return fecha_a < fecha_b
    return close_a < close_b


@cronometrar
def selection_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    n = len(arr)
    for i in range(n - 1):
        min_idx = i
        for j in range(i + 1, n):
            if es_estrictamente_menor(arr[j], arr[min_idx], simbolo=simbolo):
                min_idx = j
        if min_idx != i:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr


@cronometrar
def comb_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    n = len(arr)
    gap = n
    shrink = 1.3
    swapped = True
    while gap > 1 or swapped:
        gap = int(gap / shrink)
        if gap < 1:
            gap = 1
        swapped = False
        for i in range(0, n - gap):
            if es_estrictamente_menor(arr[i + gap], arr[i], simbolo=simbolo):
                arr[i], arr[i + gap] = arr[i + gap], arr[i]
                swapped = True
    return arr


@cronometrar
def gnome_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    n = len(arr)
    pos = 0
    while pos < n:
        if pos == 0:
            pos += 1
        elif es_estrictamente_menor(arr[pos], arr[pos - 1], simbolo=simbolo):
            arr[pos], arr[pos - 1] = arr[pos - 1], arr[pos]
            pos -= 1
        else:
            pos += 1
    return arr


@cronometrar
def binary_insertion_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    n = len(arr)
    for i in range(1, n):
        elemento_actual = arr[i]
        izquierdo = 0
        derecho = i - 1
        while izquierdo <= derecho:
            medio = (izquierdo + derecho) // 2
            if es_estrictamente_menor(
                elemento_actual,
                arr[medio],
                simbolo=simbolo,
            ):
                derecho = medio - 1
            else:
                izquierdo = medio + 1
        arr.pop(i)
        arr.insert(izquierdo, elemento_actual)
    return arr


MIN_MERGE = 32


def calcular_min_run(n):
    r = 0
    while n >= MIN_MERGE:
        r |= n & 1
        n >>= 1
    return n + r


def insertion_for_tim(arr, left, right, simbolo="VOO"):
    for i in range(left + 1, right + 1):
        temp = arr[i]
        j = i - 1
        while j >= left and es_estrictamente_menor(temp, arr[j], simbolo=simbolo):
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = temp


def merge_for_tim(arr, l, m, r, simbolo="VOO"):
    left = arr[l : m + 1]
    right = arr[m + 1 : r + 1]
    i = 0
    j = 0
    k = l
    while i < len(left) and j < len(right):
        if es_estrictamente_menor(right[j], left[i], simbolo=simbolo):
            arr[k] = right[j]
            j += 1
        else:
            arr[k] = left[i]
            i += 1
        k += 1
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1


@cronometrar
def tim_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    if not arr:
        return arr

    n = len(arr)
    min_run = calcular_min_run(n)
    for start in range(0, n, min_run):
        end = min(start + min_run - 1, n - 1)
        insertion_for_tim(arr, start, end, simbolo=simbolo)
    size = min_run
    while size < n:
        for left in range(0, n, 2 * size):
            mid = min(left + size - 1, n - 1)
            right = min(left + 2 * size - 1, n - 1)
            if mid < right:
                merge_for_tim(arr, left, mid, right, simbolo=simbolo)
        size *= 2
    return arr


def particion(arr, low, high, simbolo="VOO"):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if es_estrictamente_menor(arr[j], pivot, simbolo=simbolo):
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


@cronometrar
def quick_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    if not arr:
        return arr

    n = len(arr)
    pila = [0] * (n * 2)
    top = -1

    top += 1
    pila[top] = 0
    top += 1
    pila[top] = n - 1

    while top >= 0:
        high = pila[top]
        top -= 1
        low = pila[top]
        top -= 1

        mid = (low + high) // 2
        arr[mid], arr[high] = arr[high], arr[mid]

        p = particion(arr, low, high, simbolo=simbolo)
        if p - 1 > low:
            top += 1
            pila[top] = low
            top += 1
            pila[top] = p - 1
        if p + 1 < high:
            top += 1
            pila[top] = p + 1
            top += 1
            pila[top] = high
    return arr


def heapify(arr, n, i, simbolo="VOO"):
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if l < n and es_estrictamente_menor(arr[largest], arr[l], simbolo=simbolo):
        largest = l
    if r < n and es_estrictamente_menor(arr[largest], arr[r], simbolo=simbolo):
        largest = r
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest, simbolo=simbolo)


@cronometrar
def heap_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i, simbolo=simbolo)
    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(arr, i, 0, simbolo=simbolo)
    return arr


@cronometrar
def bucket_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    n = len(arr)
    if n == 0:
        return arr

    num_cubetas = 10
    min_val = max_val = fecha_a_entero(arr[0])
    for item in arr:
        val = fecha_a_entero(item)
        if val < min_val:
            min_val = val
        if val > max_val:
            max_val = val

    rango = (max_val - min_val + 1) / num_cubetas
    cubetas = [[] for _ in range(num_cubetas)]

    for item in arr:
        val = fecha_a_entero(item)
        idx = int((val - min_val) / rango)
        if idx == num_cubetas:
            idx -= 1
        cubetas[idx].append(item)

    resultado = []
    for cubeta in cubetas:
        for i in range(1, len(cubeta)):
            temp = cubeta[i]
            j = i - 1
            while j >= 0 and es_estrictamente_menor(temp, cubeta[j], simbolo=simbolo):
                cubeta[j + 1] = cubeta[j]
                j -= 1
            cubeta[j + 1] = temp
        resultado.extend(cubeta)
    return resultado


def radix_counting_sort(arr, exp):
    n = len(arr)
    output = [None] * n
    count = [0] * 10

    for i in range(n):
        idx = (fecha_a_entero(arr[i]) // exp) % 10
        count[idx] += 1
    for i in range(1, 10):
        count[i] += count[i - 1]

    for i in range(n - 1, -1, -1):
        idx = (fecha_a_entero(arr[i]) // exp) % 10
        output[count[idx] - 1] = arr[i]
        count[idx] -= 1
    for i in range(n):
        arr[i] = output[i]


@cronometrar
def radix_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    if not arr:
        return arr

    for i in range(1, len(arr)):
        temp = arr[i]
        j = i - 1
        while j >= 0 and obtener_cierre(temp, simbolo=simbolo) < obtener_cierre(
            arr[j],
            simbolo=simbolo,
        ):
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = temp

    max_val = fecha_a_entero(arr[0])
    for item in arr:
        valor = fecha_a_entero(item)
        if valor > max_val:
            max_val = valor

    exp = 1
    while max_val // exp > 0:
        radix_counting_sort(arr, exp)
        exp *= 10
    return arr


@cronometrar
def pigeonhole_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    if not arr:
        return arr

    min_val = max_val = fecha_a_entero(arr[0])
    for item in arr:
        val = fecha_a_entero(item)
        if val < min_val:
            min_val = val
        if val > max_val:
            max_val = val

    rango = max_val - min_val + 1
    holes = [[] for _ in range(rango)]
    for item in arr:
        holes[fecha_a_entero(item) - min_val].append(item)

    arr.clear()
    for hole in holes:
        if len(hole) > 1:
            for i in range(1, len(hole)):
                temp = hole[i]
                j = i - 1
                while j >= 0 and es_estrictamente_menor(temp, hole[j], simbolo=simbolo):
                    hole[j + 1] = hole[j]
                    j -= 1
                hole[j + 1] = temp
        arr.extend(hole)
    return arr


class NodoBST:
    def __init__(self, registro):
        self.registro = registro
        self.izq = None
        self.der = None


@cronometrar
def tree_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    if not arr:
        return []
    raiz = NodoBST(arr[0])

    for i in range(1, len(arr)):
        nuevo = arr[i]
        actual = raiz
        while True:
            if es_estrictamente_menor(nuevo, actual.registro, simbolo=simbolo):
                if actual.izq is None:
                    actual.izq = NodoBST(nuevo)
                    break
                actual = actual.izq
            else:
                if actual.der is None:
                    actual.der = NodoBST(nuevo)
                    break
                actual = actual.der

    resultado = []
    pila = []
    actual = raiz
    while pila or actual:
        if actual:
            pila.append(actual)
            actual = actual.izq
        else:
            nodo = pila.pop()
            resultado.append(nodo.registro)
            actual = nodo.der
    return resultado


def bitonic_merge(arr, low, cnt, direction, simbolo="VOO"):
    if cnt > 1:
        k = cnt // 2
        for i in range(low, low + k):
            if direction == 1 and es_estrictamente_menor(
                arr[i + k],
                arr[i],
                simbolo=simbolo,
            ):
                arr[i], arr[i + k] = arr[i + k], arr[i]
            elif direction == 0 and es_estrictamente_menor(
                arr[i],
                arr[i + k],
                simbolo=simbolo,
            ):
                arr[i], arr[i + k] = arr[i + k], arr[i]
        bitonic_merge(arr, low, k, direction, simbolo=simbolo)
        bitonic_merge(arr, low + k, k, direction, simbolo=simbolo)


def bitonic_sort_rec(arr, low, cnt, direction, simbolo="VOO"):
    if cnt > 1:
        k = cnt // 2
        bitonic_sort_rec(arr, low, k, 1, simbolo=simbolo)
        bitonic_sort_rec(arr, low + k, k, 0, simbolo=simbolo)
        bitonic_merge(arr, low, cnt, direction, simbolo=simbolo)


@cronometrar
def bitonic_sort(dataset_original, simbolo="VOO"):
    arr = dataset_original.copy()
    n = len(arr)
    if not arr:
        return arr

    potencia = 1
    while potencia < n:
        potencia *= 2

    pad = potencia - n
    if pad > 0:
        arr.extend(
            [
                {
                    "Fecha": "9999-12-31",
                    f"{simbolo}_Close": "999999.0",
                }
            ]
            * pad
        )

    bitonic_sort_rec(arr, 0, len(arr), 1, simbolo=simbolo)

    if pad > 0:
        return arr[:n]
    return arr


def obtener_top_n_volumen_y_ordenar(dataset, simbolo="VOO", limite=15):
    arr = dataset.copy()
    top_n = []
    limite_real = min(limite, len(arr))

    for _ in range(limite_real):
        max_idx = 0
        for j in range(1, len(arr)):
            vol_actual = obtener_volumen(arr[j], simbolo=simbolo)
            vol_max = obtener_volumen(arr[max_idx], simbolo=simbolo)
            if vol_actual > vol_max:
                max_idx = j
        top_n.append(arr.pop(max_idx))

    resultado_final, tiempo_ej = tim_sort(top_n, simbolo=simbolo)
    return resultado_final, tiempo_ej


ALGORITMOS = {
    "selection_sort": selection_sort,
    "comb_sort": comb_sort,
    "tim_sort": tim_sort,
    "quick_sort": quick_sort,
    "heap_sort": heap_sort,
    "tree_sort": tree_sort,
    "bucket_sort": bucket_sort,
    "radix_sort": radix_sort,
    "pigeonhole_sort": pigeonhole_sort,
    "gnome_sort": gnome_sort,
    "binary_insertion_sort": binary_insertion_sort,
    "bitonic_sort": bitonic_sort,
}


def ejecutar_benchmark(dataset, simbolo="VOO", algoritmos=None):
    nombres = algoritmos or list(ALGORITMOS.keys())
    resultados = []

    for nombre in nombres:
        funcion = ALGORITMOS[nombre]
        _, tiempo = funcion(dataset, simbolo=simbolo)
        resultados.append(
            {
                "algoritmo": nombre,
                "tiempo_ms": round(tiempo, 4),
                "registros": len(dataset),
                "simbolo": simbolo,
            }
        )

    return resultados


if __name__ == "__main__":
    print("=== PREPARANDO PISTA DE CARRERAS ===")
    mi_dataset = cargar_dataset("dataset_maestro.csv")
    simbolo_analisis = "VOO"

    if mi_dataset:
        print("\n--- INICIANDO CARRERA DE ALGORITMOS ---")
        print(f"Tamanio del dataset a ordenar: {len(mi_dataset)} registros\n")

        for nombre, funcion in ALGORITMOS.items():
            print(f"Ejecutando {nombre}...")
            _, tiempo = funcion(mi_dataset, simbolo=simbolo_analisis)
            print(f"[RESULTADO] {nombre} finalizo en {tiempo:.2f} ms.\n")

        print("=====================================================")
        print("=== EXTRAYENDO LOS 15 DIAS CON MAYOR VOLUMEN ========")
        print("=====================================================\n")

        inicio_top15 = time.perf_counter()
        top_15_ordenado, _ = obtener_top_n_volumen_y_ordenar(
            mi_dataset,
            simbolo=simbolo_analisis,
            limite=15,
        )
        fin_top15 = time.perf_counter()

        t_ms = (fin_top15 - inicio_top15) * 1000
        print(f"[OK] Extraccion y ordenamiento completado en {t_ms:.2f} ms.\n")
        print("LOS 15 DIAS MAS BUSCADOS (Ordenados cronologicamente):")

        for i, reg in enumerate(top_15_ordenado, start=1):
            fecha = reg.get("Fecha", "N/A")
            vol = obtener_volumen(reg, simbolo=simbolo_analisis)
            cierre = obtener_cierre(reg, simbolo=simbolo_analisis)
            print(
                f"  {i:02d}. Fecha: {fecha} | Volume: {vol:,.0f} | "
                f"Cierre: {cierre:.2f}"
            )
