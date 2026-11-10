"""Motor de inferencia (Laboratorio 05) para CryptoRisk & Trend SBC.

Estado del archivo:
    ✅ Implementado (tomado del lab05): TValue, TAtom, TRule, TKnowledgeBase,
       TFactBase, applies, forward, ask, deduce, backward.
    ✏️ Por completar (pseudocódigo): explain, why, DevelopmentSubsystem,
       QuerySubsystem.

Convenciones del laboratorio (NO cambiarlas):
    - TRule(name, antecedents: list[TAtom], consequent: TAtom)
    - kb.add(item) registra TAtom o TRule (los átomos primero).
    - TValue.YES = True, TValue.NO = False, TValue.UNKNOWN = "UNKNOWN"
    - Origen de un hecho: "user" o el nombre de la regla que lo dedujo.
"""


# =====================================================================
# 1. TValue — VALORES DE VERDAD
# ---------------------------------------------------------------------
# TEORÍA: la lógica proposicional clásica es bivaluada (verdadero/falso).
# Aquí usamos una lógica TRIVALENTE porque el conocimiento del mundo es
# incompleto: un indicador puede no estar disponible.
#   YES      -> la proposición se cumple.
#   NO       -> la proposición no se cumple.
#   UNKNOWN  -> "se sabe que no se sabe": el motor ya lo intentó y no pudo.
# Distinción clave: un átomo AUSENTE de la FB significa "aún no consultado";
# un átomo con UNKNOWN en la FB es una memoria que evita volver a preguntar.
# =====================================================================
class TValue:
    """Los valores para una proposición atómica."""

    YES = True
    NO = False
    UNKNOWN = "UNKNOWN"


# =====================================================================
# 2. TAtom — PROPOSICIÓN ATÓMICA
# ---------------------------------------------------------------------
# TEORÍA: una proposición atómica es una afirmación declarativa
# indivisible que puede ser verdadera o falsa (p. ej. "el RSI está por
# debajo de 30"). Se representa con:
#   symbol  -> identificador semántico (variable) usado en el código.
#   meaning -> texto en lenguaje natural, usado para preguntar al usuario
#              y para mostrar reglas legibles.
# Debe ser comparable (__eq__) y "hasheable" (__hash__) para usarse como
# clave del diccionario de hechos de la FB y como elemento de conjuntos.
# =====================================================================
class TAtom:
    """Una proposición atómica, con su variable y significado."""

    def __init__(self, symbol: str, meaning: str) -> None:
        self.symbol = symbol
        self.meaning = meaning

    def __eq__(self, atom: object) -> bool:
        if not isinstance(atom, TAtom):
            return False
        return self.symbol == atom.symbol and self.meaning == atom.meaning

    def __hash__(self):
        return hash((self.symbol, self.meaning))

    def __repr__(self) -> str:
        return f"TAtom({self.symbol!r})"


# =====================================================================
# 3. TRule — CLÁUSULA DEFINIDA DE HORN
# ---------------------------------------------------------------------
# TEORÍA: una cláusula definida de Horn tiene la forma
#       (P1 ∧ P2 ∧ ... ∧ Pn) ⇒ Q
# con UN ÚNICO literal positivo (Q) como consecuente y sólo conjunciones
# en el antecedente. Por eso una disyunción "A ∨ B ⇒ C" se modela como
# dos reglas ("A ⇒ C" y "B ⇒ C"). Cada regla lleva un identificador
# (name) que sirve para referenciarla y, sobre todo, para registrar el
# ORIGEN de los hechos que deduce: eso hace posible explicar el "cómo".
# =====================================================================
class TRule:
    """Una cláusula definida."""

    def __init__(self, name: str, antecedents: list[TAtom], consequent: TAtom) -> None:
        self.name = name
        self.antecedents = list(antecedents)
        self.consequent = consequent

    def __str__(self) -> str:
        """Representación en lenguaje natural de la regla."""
        ants = " ∧ ".join(a.meaning for a in self.antecedents)
        return f"{self.name}: {ants} -> {self.consequent.meaning}"

    def __repr__(self) -> str:
        return f"TRule({self.name!r})"


# =====================================================================
# 4. TKnowledgeBase — BASE DE CONOCIMIENTO (KB)
# ---------------------------------------------------------------------
# TEORÍA: la KB guarda el conocimiento ESTABLE del dominio (lo aporta el
# experto, no cambia entre consultas): el conjunto de proposiciones y el
# conjunto de reglas. Al agregar una regla se valida que todos sus
# átomos ya estén registrados (integridad referencial), evitando reglas
# sobre proposiciones no declaradas. Por eso el orden de carga es:
# primero átomos, después reglas.
# =====================================================================
class TKnowledgeBase:
    """La base de conocimiento: proposiciones y cláusulas definidas.

    Almacena atoms (las proposiciones del dominio) y rules (las reglas
    identificadas por su name, en orden de inserción).
    """

    def __init__(self) -> None:
        self.atoms: set[TAtom] = set()
        self.rules: dict[str, TRule] = {}

    def add(self, item: TAtom | TRule) -> None:
        """Agregar una proposición o una regla.

        Al agregar una regla, sus antecedents y su consequent ya deben
        estar registrados en atoms.

        :param item: La proposición o la regla a agregar.
        :raises ValueError: Si la regla usa proposiciones no registradas.
        """
        if isinstance(item, TAtom):
            self.atoms.add(item)
            return
        if isinstance(item, TRule):
            missing = [
                atom for atom in [*item.antecedents, item.consequent]
                if atom not in self.atoms
            ]
            if missing:
                symbols = ", ".join(atom.symbol for atom in missing)
                raise ValueError(f"Proposiciones no registradas: {symbols}")
            self.rules[item.name] = item
            return
        raise TypeError("Solo se pueden agregar TAtom o TRule")

    def obtain(self, rule_name: str) -> TRule:
        """Recuperar una regla por su identificador."""
        return self.rules[rule_name]

    def has_rule(self, rule_name: str) -> bool:
        """Conocer si un identificador de regla ya está registrado."""
        return rule_name in self.rules

    def atom(self, symbol: str) -> TAtom | None:
        """Recuperar una proposición por su symbol (None si no existe)."""
        return next((atom for atom in self.atoms if atom.symbol == symbol), None)


# =====================================================================
# 5. TFactBase — BASE DE HECHOS (FB)
# ---------------------------------------------------------------------
# TEORÍA: la FB guarda el conocimiento PARTICULAR del caso que se está
# resolviendo (cambia en cada consulta). Cada hecho = (átomo, valor,
# origen). El origen es "user" si lo dio el usuario, o el nombre de la
# regla que lo dedujo. Esta trazabilidad es la base de la explicabilidad:
# siguiendo los orígenes se reconstruye la cadena de razonamiento.
# =====================================================================
class TFactBase:
    """La base de hechos: proposiciones atómicas con su valor y origen."""

    def __init__(self) -> None:
        self.facts: dict[TAtom, tuple[TValue, str]] = {}

    def set(self, atom: TAtom, value: TValue, source: str) -> None:
        """Agregar o actualizar un hecho.

        :param atom: La proposición.
        :param value: Su valor: YES, NO o UNKNOWN.
        :param source: 'user' o el identificador de la regla que lo dedujo.
        """
        if value not in (TValue.YES, TValue.NO, TValue.UNKNOWN):
            raise ValueError("El valor debe ser YES, NO o UNKNOWN")
        self.facts[atom] = (value, source)

    def value(self, atom: TAtom) -> TValue:
        """Valor del hecho; UNKNOWN si el átomo no está en la FB."""
        fact = self.facts.get(atom)
        return fact[0] if fact is not None else TValue.UNKNOWN

    def source(self, atom: TAtom) -> str | None:
        """Origen del hecho; None si el átomo no está en la FB."""
        fact = self.facts.get(atom)
        return fact[1] if fact is not None else None


# =====================================================================
# 6. applies — ¿SE PUEDE APLICAR UNA REGLA?
# ---------------------------------------------------------------------
# TEORÍA: una regla Horn dispara (modus ponens) sólo si TODOS sus
# antecedentes son verdaderos. Con tres valores hay tres resultados:
#   YES      -> todos los antecedentes son YES: se aplica ahora.
#   NO       -> algún antecedente es NO: la regla ya nunca se aplicará.
#   UNKNOWN  -> ninguno es NO pero alguno es UNKNOWN/falta: no se puede
#               aplicar (UNKNOWN en la FB es definitivo).
# Un NO prevalece sobre un UNKNOWN (basta un antecedente falso).
# =====================================================================
def applies(kb: TKnowledgeBase, fb: TFactBase, rule: TRule) -> TValue:
    """Conocer si una regla es aplicable a la base de hechos dada.

    :return: YES si es aplicable ahora; NO si ya no podrá aplicarse;
             UNKNOWN si falta información.
    """
    has_unknown = False
    for antecedent in rule.antecedents:
        value = fb.value(antecedent)
        if value == TValue.NO:
            return TValue.NO
        if value == TValue.UNKNOWN:
            has_unknown = True
    return TValue.UNKNOWN if has_unknown else TValue.YES


# =====================================================================
# 7. forward — ENCADENAMIENTO HACIA ADELANTE
# ---------------------------------------------------------------------
# TEORÍA: razonamiento DIRIGIDO POR DATOS. Parte de los hechos conocidos
# y aplica repetidamente modus ponens a toda regla aplicable, agregando
# los consecuentes a la FB, hasta alcanzar un PUNTO FIJO (una pasada
# completa sin hechos nuevos). Deriva TODO lo deducible (descubrimiento
# de conocimiento). Cada hecho nuevo guarda como origen la regla que lo
# dedujo. Complejidad: lineal en el tamaño de la KB por pasada. Si un
# consecuente ya está en la FB no se sobrescribe (se conserva el primer
# origen, p. ej. R3 antes que R4).
# =====================================================================
def forward(kb: TKnowledgeBase, fb: TFactBase) -> TFactBase:
    """Inferencia hacia adelante.

    :return: La FB actualizada; cada hecho nuevo tiene como origen el
             identificador de su regla.
    """
    changed = True
    while changed:
        changed = False
        for rule in kb.rules.values():
            if applies(kb, fb, rule) != TValue.YES:
                continue
            if rule.consequent in fb.facts:
                continue
            fb.set(rule.consequent, TValue.YES, rule.name)
            changed = True
    return fb


# =====================================================================
# 8. ask — PREGUNTAR AL USUARIO
# ---------------------------------------------------------------------
# TEORÍA: en el razonamiento hacia atrás, si una proposición no es
# consecuente de ninguna regla (es un dato de ENTRADA) el sistema no
# puede deducirla; la única fuente es el usuario. ask muestra el
# `meaning` y valida la respuesta (YES/NO/UNKNOWN), insistiendo hasta
# recibir una válida. Responder UNKNOWN es legítimo y se recuerda.
# =====================================================================
def ask(p: TAtom) -> TValue:
    """Preguntar al usuario por el valor de una proposición atómica."""
    values = {
        "YES": TValue.YES,
        "NO": TValue.NO,
        "UNKNOWN": TValue.UNKNOWN,
    }
    while True:
        answer = input(f"{p.meaning} (YES/NO/UNKNOWN): ").strip().upper()
        if answer in values:
            return values[answer]


# =====================================================================
# 9. deduce — REGLAS QUE CONCLUYEN UNA PROPOSICIÓN
# ---------------------------------------------------------------------
# TEORÍA: paso básico del razonamiento hacia atrás: dada una meta p,
# se buscan las reglas cuyo consecuente es p. Si hay varias, cada una es
# una VÍA ALTERNATIVA para probar p (como R3 y R4 para oportunidad_compra).
# Si no hay ninguna, p es un dato de entrada (se pregunta al usuario).
# =====================================================================
def deduce(kb: TKnowledgeBase, p: TAtom) -> list[TRule]:
    """Las reglas cuyo consecuente es p."""
    return [rule for rule in kb.rules.values() if rule.consequent == p]


# =====================================================================
# 10. backward — ENCADENAMIENTO HACIA ATRÁS
# ---------------------------------------------------------------------
# TEORÍA: razonamiento DIRIGIDO POR OBJETIVOS. Parte de una meta y la
# prueba recursivamente: busca las reglas que la concluyen y convierte
# sus antecedentes en submetas. Sólo toca lo necesario y sólo pregunta
# al usuario por datos de entrada que realmente influyen. Detalles:
#   - Memoria: si la meta ya está en la FB (incluso UNKNOWN) se devuelve
#     su valor sin repetir trabajo ni preguntar de nuevo.
#   - Si la meta no es consecuente de ninguna regla -> ask().
#   - Con varias reglas se prueban en orden; la primera cuyos
#     antecedentes sean TODOS YES prueba la meta (origen = esa regla).
#   - `all(...)` hace cortocircuito: tras un antecedente no-YES ya no se
#     preguntan los restantes de esa regla.
#   - Si ninguna regla logra probarla, el resultado es UNKNOWN (este
#     motor nunca devuelve NO para una meta deducible).
#   - `active` evita ciclos infinitos en reglas circulares.
# =====================================================================
def backward(
    kb: TKnowledgeBase, fb: TFactBase, p: TAtom
) -> tuple[TValue, TFactBase]:
    """Inferencia hacia atrás.

    :return: El valor de p y la base de hechos actualizada.
    """
    active: set[TAtom] = set()

    def infer(goal: TAtom) -> TValue:
        if goal in fb.facts:
            return fb.value(goal)
        if goal in active:
            return TValue.UNKNOWN

        rules = deduce(kb, goal)
        if not rules:
            value = ask(goal)
            fb.set(goal, value, "user")
            return value

        active.add(goal)
        try:
            for rule in rules:
                if all(infer(antecedent) == TValue.YES for antecedent in rule.antecedents):
                    fb.set(goal, TValue.YES, rule.name)
                    return TValue.YES
            return TValue.UNKNOWN
        finally:
            active.remove(goal)

    return infer(p), fb


# =====================================================================
# 11. explain — EL "CÓMO" DE UNA CONCLUSIÓN            ✏️ POR COMPLETAR
# ---------------------------------------------------------------------
# TEORÍA: un SBC debe justificar sus conclusiones. Como cada hecho de la
# FB guarda su origen, la explicación es un recorrido recursivo del
# "árbol de prueba": desde la conclusión se sigue la regla que la
# produjo, se explican sus antecedentes, y se termina en las HOJAS, que
# son hechos con origen "user". El resultado responde "¿cómo concluiste
# esto?" mostrando la secuencia de reglas encadenadas. La sangría
# (level) refleja la profundidad en el árbol.
# =====================================================================
def explain(kb: TKnowledgeBase, fb: TFactBase, p: TAtom, level: int = 0) -> str:
    """CÓMO: recorre los orígenes de la FB desde p hasta los hechos del usuario."""
    # PSEUDOCODIGO:
    #   origen = fb.source(p)
    #   línea = sangría(level) + p.symbol + " = " + valor + "  <- " + origen
    #   si origen es None -> "no está en la FB"
    #   si origen == "user" -> retornar línea (hoja)
    #   si no: regla = kb.obtain(origen)
    #       para cada antecedente de la regla:
    #           línea += "\n" + explain(kb, fb, antecedente, level + 1)
    #   retornar línea
    raise NotImplementedError


# =====================================================================
# 12. why — EL "POR QUÉ" DE UNA PREGUNTA              ✏️ POR COMPLETAR
# ---------------------------------------------------------------------
# TEORÍA: complemento del "cómo". Mientras el "cómo" explica una
# conclusión ya obtenida, el "por qué" justifica una PREGUNTA que el
# sistema hace al usuario: indica qué regla necesita ese dato y qué meta
# se persigue con ella. Se obtiene subiendo por las reglas donde el
# átomo preguntado es antecedente hasta llegar a la meta consultada.
# Aumenta la confianza del usuario y evita preguntas "misteriosas".
# =====================================================================
def why(kb: TKnowledgeBase, goal: TAtom, asked: TAtom) -> str:
    """POR QUÉ se pregunta `asked` mientras se persigue `goal`."""
    # PSEUDOCODIGO:
    #   buscar reglas donde `asked` es antecedente y que (transitivamente)
    #   conducen a `goal` (subir por los consecuentes hasta llegar a goal)
    #   retornar texto "Pregunto X porque R? lo necesita para Y ... para goal"
    raise NotImplementedError


# =====================================================================
# 13. DevelopmentSubsystem — SUBSISTEMA DE DESARROLLO  ✏️ POR COMPLETAR
# ---------------------------------------------------------------------
# TEORÍA: arquitectura clásica de un SBC con dos subsistemas separados:
#   - DESARROLLO (lo usa el EXPERTO): adquisición y edición del
#     conocimiento estable (átomos y reglas) -> construye la KB.
#   - CONSULTA (lo usa el USUARIO): usa la KB para deducir y explicar.
# Separarlos permite que el experto cambie el conocimiento sin tocar el
# motor, y que el usuario consulte sin poder alterar la KB. Este
# subsistema debe validar la entrada (la KB ya rechaza reglas con
# átomos no registrados con ValueError).
# =====================================================================
class DevelopmentSubsystem:
    """Subsistema de desarrollo: construir la KB (lo usa el experto)."""

    def __init__(self, kb: TKnowledgeBase) -> None:
        # TODO: guardar kb en self.kb
        raise NotImplementedError

    def add_atom(self) -> None:
        # PSEUDOCODIGO: pedir symbol y meaning; kb.add(TAtom(...))
        raise NotImplementedError

    def add_rule(self) -> None:
        # PSEUDOCODIGO: pedir name, antecedentes (symbols separados por coma)
        #   y consecuente; resolverlos con kb.atom(); kb.add(TRule(...));
        #   capturar ValueError y mostrar el mensaje
        raise NotImplementedError

    def show(self) -> None:
        # PSEUDOCODIGO: imprimir átomos y reglas (str(regla))
        raise NotImplementedError

    def reset(self) -> None:
        # PSEUDOCODIGO: vaciar kb.atoms y kb.rules
        raise NotImplementedError

    def run(self) -> None:
        # PSEUDOCODIGO: bucle de menú 1) átomo 2) regla 3) mostrar 4) reiniciar 0) salir
        raise NotImplementedError


# =====================================================================
# 14. QuerySubsystem — SUBSISTEMA DE CONSULTA          ✏️ POR COMPLETAR
# ---------------------------------------------------------------------
# TEORÍA: es la cara del SBC hacia el usuario final. Trabaja sobre la FB
# (conocimiento particular del caso) y ofrece los servicios del motor:
# registrar hechos observados, inferir hacia adelante (descubrir),
# responder una meta hacia atrás (con preguntas) y explicar el cómo.
# Reiniciar la consulta vacía la FB sin tocar la KB, de modo que el mismo
# conocimiento sirve para muchos casos.
# =====================================================================
class QuerySubsystem:
    """Subsistema de consulta: usar el conocimiento (lo usa el usuario)."""

    def __init__(self, kb: TKnowledgeBase, fb: TFactBase) -> None:
        # TODO: guardar kb y fb
        raise NotImplementedError

    def add_fact(self) -> None:
        # PSEUDOCODIGO: pedir symbol y valor (YES/NO/UNKNOWN); fb.set(..., "user")
        raise NotImplementedError

    def infer(self) -> None:
        # PSEUDOCODIGO: copiar claves previas, forward(kb, fb), mostrar hechos nuevos
        raise NotImplementedError

    def answer(self) -> None:
        # PSEUDOCODIGO: pedir meta; backward(kb, fb, meta); mostrar valor
        raise NotImplementedError

    def how(self) -> None:
        # PSEUDOCODIGO: pedir conclusión; imprimir explain(kb, fb, atomo)
        raise NotImplementedError

    def show(self) -> None:
        # PSEUDOCODIGO: imprimir cada hecho: symbol = valor (origen)
        raise NotImplementedError

    def reset(self) -> None:
        # PSEUDOCODIGO: vaciar fb.facts (sin tocar la KB)
        raise NotImplementedError

    def run(self) -> None:
        # PSEUDOCODIGO: bucle de menú con las opciones anteriores
        raise NotImplementedError
